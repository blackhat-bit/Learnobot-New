// lib/services/auth_service.dart

import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Registration: Creates user in Firebase Auth AND saves extra data in Firestore
  Future<UserCredential> registerWithEmail({
    required String email,
    required String password,
    required String username,
    required String role, // 'Teacher' or 'Student'
  }) async {
    // Register user in Firebase Auth
    final userCredential = await _auth.createUserWithEmailAndPassword(
      email: email,
      password: password,
    );

    // Save user data to Firestore (users collection)
    await _firestore.collection('users').doc(userCredential.user!.uid).set({
      'username': username,
      'email': email,
      'role': role,
    });

    return userCredential;
  }

  // Login with Email/Password
  Future<UserCredential> loginWithEmail({
    required String email,
    required String password,
  }) async {
    return await _auth.signInWithEmailAndPassword(
      email: email,
      password: password,
    );
  }

  // Login and check role (returns username if correct, null if wrong role)
  Future<String?> loginAndCheckRole({
    required String email,
    required String password,
    required String role, // 'Teacher' or 'Student'
  }) async {
    final userCredential =
        await loginWithEmail(email: email, password: password);
    final uid = userCredential.user!.uid;
    final doc = await _firestore.collection('users').doc(uid).get();

    if (doc.exists && doc['role'] == role) {
      return doc['username'] as String;
    }
    // Optionally sign out if role mismatch
    await signOut();
    return null;
  }

  // Get current user's role
  Future<String?> getCurrentUserRole() async {
    final user = _auth.currentUser;
    if (user == null) return null;
    final doc = await _firestore.collection('users').doc(user.uid).get();
    return doc.exists ? doc['role'] as String : null;
  }

  // Get current user's data
  Future<Map<String, dynamic>?> getCurrentUserData() async {
    final user = _auth.currentUser;
    if (user == null) return null;
    final doc = await _firestore.collection('users').doc(user.uid).get();
    return doc.exists ? doc.data() : null;
  }

  // Get current user's username
  Future<String?> getCurrentUserName() async {
    final userData = await getCurrentUserData();
    return userData?['username'] as String?;
  }

  // Sign out
  Future<void> signOut() async {
    await _auth.signOut();
  }
}
