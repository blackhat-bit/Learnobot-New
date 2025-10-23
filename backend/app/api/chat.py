# app/api/chat.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas import chat as chat_schemas
from app.services import chat_service, ocr_service
from app.models.user import User, UserRole
import base64
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/sessions", response_model=chat_schemas.ChatSession)
async def create_chat_session(
    session_data: chat_schemas.ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session - Students and Admins allowed"""
    
    # Admin can create sessions for testing - create virtual admin student profile
    if current_user.role == UserRole.ADMIN:
        from app.models.user import StudentProfile
        
        # Check if admin already has a virtual student profile
        admin_student_profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == current_user.id
        ).first()
        
        if not admin_student_profile:
            # Create virtual student profile for admin testing
            admin_student_profile = StudentProfile(
                user_id=current_user.id,
                full_name=f"Admin Testing ({current_user.username})",
                grade="Admin",
                difficulty_level=5,  # Advanced level for admin
                difficulties_description="Admin testing account"
            )
            db.add(admin_student_profile)
            db.commit()
            db.refresh(admin_student_profile)
        
        return await chat_service.create_session(
            db=db,
            student_id=admin_student_profile.id,
            mode=session_data.mode
        )
    
    # Regular student flow
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students and admins can create chat sessions")
    
    if not current_user.student_profile:
        raise HTTPException(status_code=400, detail="Student profile not found")
    
    return await chat_service.create_session(
        db=db,
        student_id=current_user.student_profile.id,
        mode=session_data.mode
    )

@router.post("/sessions/{session_id}/messages", response_model=chat_schemas.ChatMessage)
async def send_message(
    session_id: int,
    message: chat_schemas.ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message in a chat session and get AI response"""
    return await chat_service.process_message(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
        message=message.content,
        assistance_type=message.assistance_type,
        provider=message.provider
    )

@router.post("/test-ocr")
async def test_ocr(file: UploadFile = File(...)):
    """Test OCR alone without any AI processing"""
    import time
    start = time.time()
    content = await file.read()
    extracted = await ocr_service.extract_text(content)
    ocr_time = time.time() - start
    logger.info(f"OCR test completed in {ocr_time:.2f}s, extracted {len(extracted)} chars")
    return {
        "ocr_time_seconds": round(ocr_time, 2),
        "extracted_text": extracted,
        "text_length": len(extracted)
    }

@router.post("/test-vision")
async def test_vision(
    file: UploadFile = File(...),
    provider: str = "google-gemini_2_5_pro"
):
    """Test Vision API alone"""
    import time
    from app.services.vision_service import vision_service
    
    start = time.time()
    content = await file.read()
    
    logger.info(f"Testing vision with provider: {provider}, image size: {len(content)} bytes")
    
    result = await vision_service.process_image_with_vision(
        image_data=content,
        prompt="מה כתוב בתמונה הזו? תאר בעברית.",
        provider=provider
    )
    
    vision_time = time.time() - start
    logger.info(f"Vision test completed in {vision_time:.2f}s")
    
    return {
        "vision_time_seconds": round(vision_time, 2),
        "success": result.get("success"),
        "response": result.get("response"),
        "error": result.get("error")
    }

@router.post("/sessions/{session_id}/upload-task")
async def upload_task(
    session_id: int,
    files: List[UploadFile] = File(...),
    provider: str = Form(None),
    text_description: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload one or more images of a task with optional text description - uses Vision API for cloud models, OCR for local models"""
    import time
    import asyncio
    from app.services.vision_service import vision_service
    from pathlib import Path
    import uuid
    
    logger.info(f"=== UPLOAD REQUEST RECEIVED === Session: {session_id}, Provider: {provider}, Files: {len(files)}, Description: {text_description}")
    
    start_time = time.time()
    
    # Process all images
    image_contents = []
    image_urls = []
    upload_dir = Path("uploads/task_images")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        # Check content type or file extension
        is_image = (
            file.content_type and file.content_type.startswith("image/")
        ) or (
            file.filename and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
        )

        if not is_image:
            raise HTTPException(status_code=400, detail=f"File {file.filename} must be an image")
        
        # Read file content
        content = await file.read()
        logger.info(f"Image received: {len(content)} bytes, {file.filename}")
        image_contents.append(content)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix if file.filename else '.jpg'
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename
        
        # Write image to disk
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Generate URL path
        image_url = f"/uploads/task_images/{unique_filename}"
        image_urls.append(image_url)
        logger.info(f"Image saved to: {file_path}, URL: {image_url}")
    
    # Use first image as primary image for backward compatibility
    content = image_contents[0]
    image_url = image_urls[0]
    
    # Check if provider supports vision
    is_cloud_model = provider and vision_service.supports_vision(provider)
    logger.info(f"Provider: {provider}, Supports Vision: {vision_service.supports_vision(provider) if provider else False}, Is Cloud: {is_cloud_model}")
    
    if is_cloud_model:
        # ===== VISION API PATH (Fast - for cloud models, NO OCR) =====
        logger.info(f"Using Vision API with provider: {provider} (OCR disabled)")
        
        # Create Hebrew prompt for vision model
        base_prompt = """קרא את הטקסט בתמונה{multiple} ועזור לתלמיד להבין את המשימה.

{description}

אם יש טקסט בתמונה:
1. תאר מה רשום בתמונה (רק הטקסט הרלוונטי למשימה)
2. הסבר במילים פשוטות מה צריך לעשות
3. שאל את התלמיד איך תרצה שאעזור (הסבר, פירוק לשלבים, או דוגמה)

אם אין טקסט ברור:
תגיד לתלמיד שלא הצלחת לקרוא את התמונה בבירור ותבקש להעלות תמונה ברורה יותר.

תענה בעברית פשוטה וברורה. אל תתחיל בברכה או הצגה - תתחיל ישירות עם התשובה."""
        
        # Add context from text description if provided
        description_text = ""
        if text_description:
            description_text = f"התלמיד אמר: \"{text_description}\"\n"
        
        # Indicate if multiple images
        multiple_text = "" if len(files) == 1 else " (יש מספר תמונות)"
        
        vision_prompt = base_prompt.format(
            description=description_text,
            multiple=multiple_text
        )
        
        # Process with vision (fast!) - process ALL images
        vision_start = time.time()
        try:
            # For multiple images, we'll process them one by one and combine results
            if len(image_contents) > 1:
                all_responses = []
                for i, img_content in enumerate(image_contents):
                    logger.info(f"Processing image {i+1}/{len(image_contents)} with vision API")
                    vision_result = await vision_service.process_image_with_vision(
                        image_data=img_content,
                        prompt=vision_prompt,
                        provider=provider
                    )
                    if vision_result.get("success"):
                        all_responses.append(f"תמונה {i+1}: {vision_result['response']}")
                    else:
                        all_responses.append(f"תמונה {i+1}: שגיאה - {vision_result.get('error', 'Unknown error')}")
                
                # Combine all responses
                combined_response = "\n\n".join(all_responses)
                vision_result = {
                    "success": True,
                    "response": combined_response
                }
            else:
                # Single image - use original logic
                vision_result = await vision_service.process_image_with_vision(
                    image_data=content,
                    prompt=vision_prompt,
                    provider=provider
                )
            vision_time = time.time() - vision_start
            
            if not vision_result.get("success"):
                raise ValueError(vision_result.get("error", "Vision processing failed"))
            
            ai_response_text = vision_result["response"]
            logger.info(f"Vision API completed in {vision_time:.2f}s")
            
            # For cloud models: Save AI's interpretation as the "extracted text"
            # The AI describes what's in the image, so we save that instead of OCR
            extracted_text = ai_response_text
            
            # Save task with AI's vision response (no OCR needed)
            task = await chat_service.process_task_image(
                db=db,
                session_id=session_id,
                student_id=current_user.student_profile.id,
                image_data=content,
                extracted_text=extracted_text,
                image_url=image_url
            )
            
            # Save AI response to chat
            from app.models.chat import ChatMessage, MessageRole
            ai_response = ChatMessage(
                session_id=session_id,
                user_id=current_user.id,
                role=MessageRole.ASSISTANT,
                content=ai_response_text
            )
            db.add(ai_response)
            db.commit()
            db.refresh(ai_response)
            
            total_time = time.time() - start_time
            logger.info(f"✅ Vision path: {vision_time:.2f}s vision | {total_time:.2f}s total")
            
            return {
                "task_id": task.id,
                "extracted_text": extracted_text,
                "ai_response": ai_response.content,
                "message": "קראתי את התמונה בהצלחה!",
                "processing_time_seconds": round(total_time, 2),
                "method": "vision",
                "image_url": image_url,  # Primary image (backward compat)
                "image_urls": image_urls  # All images
            }
            
        except Exception as e:
            logger.error(f"Vision API failed: {str(e)}, falling back to OCR")
            # Fall through to OCR path
            is_cloud_model = False
    
    if not is_cloud_model:
        # ===== OCR PATH (for local models or vision fallback) =====
        logger.info(f"Using OCR path for provider: {provider or 'default'}")
        
        ocr_start = time.time()
        # Process ALL images with OCR
        all_extracted_texts = []
        for i, img_content in enumerate(image_contents):
            logger.info(f"Processing image {i+1}/{len(image_contents)} with OCR")
            img_extracted = await ocr_service.extract_text(img_content)
            if img_extracted and not img_extracted.startswith("לא הצלחתי") and not img_extracted.startswith("שגיאה"):
                all_extracted_texts.append(f"תמונה {i+1}:\n{img_extracted}")
            else:
                all_extracted_texts.append(f"תמונה {i+1}: לא הצלחתי לקרוא את הטקסט")
        
        # Combine all extracted texts
        extracted_text = "\n\n".join(all_extracted_texts)
        ocr_time = time.time() - ocr_start
        logger.info(f"OCR completed in {ocr_time:.2f}s for {len(image_contents)} images")
        
        # Process with Hebrew mediation if text was extracted successfully
        if extracted_text and not extracted_text.startswith("לא הצלחתי") and not extracted_text.startswith("שגיאה"):
            # Save task
            task = await chat_service.process_task_image(
                db=db,
                session_id=session_id,
                student_id=current_user.student_profile.id,
                image_data=content,
                extracted_text=extracted_text,
                image_url=image_url
            )
            
            # Process extracted text through AI system
            try:
                logger.info(f"Processing OCR text (length: {len(extracted_text)}): {extracted_text[:100]}...")
                
                ai_start = time.time()
                ai_response = await chat_service.process_message(
                    db=db,
                    session_id=session_id,
                    user_id=current_user.id,
                    message=extracted_text,
                    assistance_type=None,
                    provider=provider
                )
                ai_time = time.time() - ai_start
                total_time = time.time() - start_time
                logger.info(f"OCR path: {ocr_time:.2f}s OCR + {ai_time:.2f}s AI = {total_time:.2f}s total")
            except Exception as e:
                logger.error(f"Error in AI processing for OCR: {str(e)}")
                # Create a fallback response
                from app.models.chat import ChatMessage, MessageRole
                ai_response = ChatMessage(
                    session_id=session_id,
                    user_id=current_user.id,
                    role=MessageRole.ASSISTANT,
                    content=f"קראתי את הטקסט: {extracted_text}\n\nאיך תרצה שאעזור לך עם זה?"
                )
                db.add(ai_response)
                db.commit()
                db.refresh(ai_response)
                total_time = time.time() - start_time
            
            return {
                "task_id": task.id,
                "extracted_text": extracted_text,
                "ai_response": ai_response.content,
                "message": "קראתי את התמונה בהצלחה!",
                "processing_time_seconds": round(total_time, 2),
                "method": "ocr",
                "image_url": image_url,  # Primary image (backward compat)
                "image_urls": image_urls  # All images
            }
        else:
            # OCR failed, return error message  
            return {
                "task_id": None,
                "extracted_text": extracted_text,
                "ai_response": None,
                "message": extracted_text,
                "method": "ocr",
                "image_url": image_url if image_urls else None,  # Primary image
                "image_urls": image_urls  # All images
            }

@router.put("/messages/{message_id}/rate")
async def rate_message(
    message_id: int,
    rating_data: chat_schemas.RatingSatisfaction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rate an AI response"""
    return chat_service.rate_message(
        db=db,
        message_id=message_id,
        rating=rating_data.rating,
        user_id=current_user.id
    )

@router.post("/sessions/{session_id}/end")
async def end_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End a chat session"""
    
    # Check if session exists and user has access
    from app.models.chat import ChatSession
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check permissions
    if current_user.role == UserRole.ADMIN:
        # Admin can end any session
        pass
    elif current_user.role == UserRole.STUDENT:
        # Student can only end their own sessions
        if not current_user.student_profile or session.student_id != current_user.student_profile.id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=403, detail="Only students and admins can end sessions")
    
    # End the session
    await chat_service.end_session(db=db, session_id=session_id)
    
    return {"message": "Session ended successfully"}

@router.post("/call-teacher/{session_id}")
async def call_teacher(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a help request to the teacher"""
    
    # Handle admin users - they can call teacher for any session (including their own)
    if current_user.role == UserRole.ADMIN:
        # Get the session to find the student (could be admin's own virtual profile)
        from app.models.chat import ChatSession
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        student_id = session.student_id
    else:
        # Regular student flow
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(status_code=403, detail="Only students and admins can call teachers")
        
        if not current_user.student_profile:
            raise HTTPException(status_code=400, detail="Student profile not found")
        
        student_id = current_user.student_profile.id
    
    return await chat_service.call_teacher(
        db=db,
        session_id=session_id,
        student_id=student_id
    )

