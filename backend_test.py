#!/usr/bin/env python3
"""
Backend API Testing for Mini Quiz Platform
Tests all quiz management, attempt submission, and result retrieval endpoints
"""

import requests
import json
import time
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from frontend environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE_URL = f"{BACKEND_URL}/api"

class QuizPlatformTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.session = requests.Session()
        self.created_quiz_id = None
        self.created_result_id = None
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results"""
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        print()

    def test_health_check(self) -> bool:
        """Test GET /api/ - Health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "status" in data:
                    self.log_test("Health Check", "PASS", f"API is running: {data['message']}")
                    return True
                else:
                    self.log_test("Health Check", "FAIL", "Response missing required fields")
                    return False
            else:
                self.log_test("Health Check", "FAIL", f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", "FAIL", f"Exception: {str(e)}")
            return False

    def test_create_quiz(self) -> bool:
        """Test POST /api/quizzes - Create new quiz"""
        try:
            # Create a comprehensive quiz with realistic data
            quiz_data = {
                "title": "Introduction to Python Programming",
                "subject": "Computer Science",
                "description": "Basic concepts and syntax of Python programming language",
                "time_limit": 30,
                "questions": [
                    {
                        "question_text": "What is the correct way to create a list in Python?",
                        "question_type": "multiple_choice",
                        "options": ["list = []", "list = {}", "list = ()", "list = <>"],
                        "correct_answer": "list = []",
                        "explanation": "Square brackets [] are used to create lists in Python"
                    },
                    {
                        "question_text": "Which keyword is used to define a function in Python?",
                        "question_type": "multiple_choice", 
                        "options": ["function", "def", "func", "define"],
                        "correct_answer": "def",
                        "explanation": "The 'def' keyword is used to define functions in Python"
                    },
                    {
                        "question_text": "What does the len() function return?",
                        "question_type": "multiple_choice",
                        "options": ["The length of an object", "The type of an object", "The value of an object", "The memory address"],
                        "correct_answer": "The length of an object",
                        "explanation": "len() returns the number of items in an object like string, list, tuple, etc."
                    }
                ]
            }
            
            response = self.session.post(
                f"{self.base_url}/quizzes",
                json=quiz_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "title", "subject", "questions", "total_questions"]
                
                if all(field in data for field in required_fields):
                    self.created_quiz_id = data["id"]
                    if data["total_questions"] == len(quiz_data["questions"]):
                        self.log_test("Create Quiz", "PASS", f"Quiz created with ID: {self.created_quiz_id}")
                        return True
                    else:
                        self.log_test("Create Quiz", "FAIL", "Total questions count mismatch")
                        return False
                else:
                    self.log_test("Create Quiz", "FAIL", "Response missing required fields")
                    return False
            else:
                self.log_test("Create Quiz", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Quiz", "FAIL", f"Exception: {str(e)}")
            return False

    def test_list_quizzes(self) -> bool:
        """Test GET /api/quizzes - List all quizzes"""
        try:
            response = self.session.get(f"{self.base_url}/quizzes")
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    if len(data) > 0:
                        # Check if our created quiz is in the list
                        quiz_found = False
                        for quiz in data:
                            if quiz.get("id") == self.created_quiz_id:
                                quiz_found = True
                                # Verify that questions are not included in listing
                                if "questions" not in quiz:
                                    self.log_test("List Quizzes", "PASS", f"Found {len(data)} quizzes, questions properly hidden")
                                    return True
                                else:
                                    self.log_test("List Quizzes", "FAIL", "Questions should not be included in quiz listing")
                                    return False
                        
                        if not quiz_found:
                            self.log_test("List Quizzes", "FAIL", "Created quiz not found in listing")
                            return False
                    else:
                        self.log_test("List Quizzes", "PASS", "Empty quiz list returned")
                        return True
                else:
                    self.log_test("List Quizzes", "FAIL", "Response is not a list")
                    return False
            else:
                self.log_test("List Quizzes", "FAIL", f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("List Quizzes", "FAIL", f"Exception: {str(e)}")
            return False

    def test_get_quiz_for_taking(self) -> bool:
        """Test GET /api/quizzes/{quiz_id} - Get quiz for taking"""
        try:
            if not self.created_quiz_id:
                self.log_test("Get Quiz for Taking", "FAIL", "No quiz ID available for testing")
                return False
                
            response = self.session.get(f"{self.base_url}/quizzes/{self.created_quiz_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["id", "title", "subject", "questions"]
                if all(field in data for field in required_fields):
                    # Verify that correct answers are hidden
                    questions = data["questions"]
                    answers_hidden = True
                    
                    for question in questions:
                        if "correct_answer" in question or "explanation" in question:
                            answers_hidden = False
                            break
                        
                        # Verify required fields are present
                        required_q_fields = ["id", "question_text", "question_type", "options"]
                        if not all(field in question for field in required_q_fields):
                            self.log_test("Get Quiz for Taking", "FAIL", "Question missing required fields")
                            return False
                    
                    if answers_hidden:
                        self.log_test("Get Quiz for Taking", "PASS", "Quiz retrieved with answers properly hidden")
                        return True
                    else:
                        self.log_test("Get Quiz for Taking", "FAIL", "Correct answers not properly hidden")
                        return False
                else:
                    self.log_test("Get Quiz for Taking", "FAIL", "Response missing required fields")
                    return False
            else:
                self.log_test("Get Quiz for Taking", "FAIL", f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Get Quiz for Taking", "FAIL", f"Exception: {str(e)}")
            return False

    def test_invalid_quiz_retrieval(self) -> bool:
        """Test GET /api/quizzes/{invalid_id} - Invalid quiz ID"""
        try:
            invalid_id = "non-existent-quiz-id"
            response = self.session.get(f"{self.base_url}/quizzes/{invalid_id}")
            
            if response.status_code == 404:
                self.log_test("Invalid Quiz Retrieval", "PASS", "Properly returns 404 for invalid quiz ID")
                return True
            else:
                self.log_test("Invalid Quiz Retrieval", "FAIL", f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Invalid Quiz Retrieval", "FAIL", f"Exception: {str(e)}")
            return False

    def test_submit_quiz_attempt(self) -> bool:
        """Test POST /api/quizzes/{quiz_id}/attempt - Submit quiz responses"""
        try:
            if not self.created_quiz_id:
                self.log_test("Submit Quiz Attempt", "FAIL", "No quiz ID available for testing")
                return False
            
            # First get the quiz to know question IDs
            quiz_response = self.session.get(f"{self.base_url}/quizzes/{self.created_quiz_id}")
            if quiz_response.status_code != 200:
                self.log_test("Submit Quiz Attempt", "FAIL", "Could not retrieve quiz for attempt")
                return False
                
            quiz_data = quiz_response.json()
            questions = quiz_data["questions"]
            
            # Create responses (mix of correct and incorrect answers)
            responses = []
            for i, question in enumerate(questions):
                if i == 0:  # First question - correct answer
                    responses.append({
                        "question_id": question["id"],
                        "selected_answer": "list = []"  # Correct answer
                    })
                elif i == 1:  # Second question - correct answer
                    responses.append({
                        "question_id": question["id"],
                        "selected_answer": "def"  # Correct answer
                    })
                else:  # Third question - incorrect answer
                    responses.append({
                        "question_id": question["id"],
                        "selected_answer": "The type of an object"  # Incorrect answer
                    })
            
            attempt_data = {
                "responses": responses,
                "time_taken": 1200  # 20 minutes in seconds
            }
            
            response = self.session.post(
                f"{self.base_url}/quizzes/{self.created_quiz_id}/attempt",
                json=attempt_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                required_fields = ["id", "quiz_id", "score", "total_questions", "percentage", 
                                 "correct_answers", "incorrect_answers", "detailed_results"]
                
                if all(field in result for field in required_fields):
                    # Verify scoring calculation
                    expected_score = 2  # 2 correct out of 3
                    expected_percentage = round((2/3) * 100, 2)
                    
                    if (result["score"] == expected_score and 
                        result["correct_answers"] == expected_score and
                        result["incorrect_answers"] == 1 and
                        result["percentage"] == expected_percentage):
                        
                        # Verify detailed results
                        detailed_results = result["detailed_results"]
                        if len(detailed_results) == 3:
                            self.created_result_id = result["id"]
                            self.log_test("Submit Quiz Attempt", "PASS", 
                                        f"Score: {result['score']}/{result['total_questions']} ({result['percentage']}%)")
                            return True
                        else:
                            self.log_test("Submit Quiz Attempt", "FAIL", "Detailed results count mismatch")
                            return False
                    else:
                        self.log_test("Submit Quiz Attempt", "FAIL", 
                                    f"Scoring calculation error. Got: {result['score']}/{result['total_questions']}")
                        return False
                else:
                    self.log_test("Submit Quiz Attempt", "FAIL", "Response missing required fields")
                    return False
            else:
                self.log_test("Submit Quiz Attempt", "FAIL", f"Status code: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Submit Quiz Attempt", "FAIL", f"Exception: {str(e)}")
            return False

    def test_get_quiz_result(self) -> bool:
        """Test GET /api/results/{result_id} - Get specific quiz result"""
        try:
            if not self.created_result_id:
                self.log_test("Get Quiz Result", "FAIL", "No result ID available for testing")
                return False
                
            response = self.session.get(f"{self.base_url}/results/{self.created_result_id}")
            
            if response.status_code == 200:
                result = response.json()
                
                required_fields = ["id", "quiz_id", "quiz_title", "score", "percentage", "detailed_results"]
                if all(field in result for field in required_fields):
                    # Verify detailed results include explanations
                    detailed_results = result["detailed_results"]
                    explanations_present = all("explanation" in dr for dr in detailed_results)
                    correct_answers_present = all("correct_answer" in dr for dr in detailed_results)
                    
                    if explanations_present and correct_answers_present:
                        self.log_test("Get Quiz Result", "PASS", "Result retrieved with complete details")
                        return True
                    else:
                        self.log_test("Get Quiz Result", "FAIL", "Detailed results missing explanations or correct answers")
                        return False
                else:
                    self.log_test("Get Quiz Result", "FAIL", "Response missing required fields")
                    return False
            else:
                self.log_test("Get Quiz Result", "FAIL", f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Get Quiz Result", "FAIL", f"Exception: {str(e)}")
            return False

    def test_get_all_results_admin(self) -> bool:
        """Test GET /api/admin/results - Get all quiz results for admin"""
        try:
            response = self.session.get(f"{self.base_url}/admin/results")
            
            if response.status_code == 200:
                results = response.json()
                
                if isinstance(results, list):
                    if len(results) > 0:
                        # Check if our result is in the list
                        result_found = any(result.get("id") == self.created_result_id for result in results)
                        
                        if result_found:
                            self.log_test("Get All Results (Admin)", "PASS", f"Found {len(results)} results")
                            return True
                        else:
                            self.log_test("Get All Results (Admin)", "FAIL", "Created result not found in admin results")
                            return False
                    else:
                        self.log_test("Get All Results (Admin)", "PASS", "Empty results list returned")
                        return True
                else:
                    self.log_test("Get All Results (Admin)", "FAIL", "Response is not a list")
                    return False
            else:
                self.log_test("Get All Results (Admin)", "FAIL", f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Get All Results (Admin)", "FAIL", f"Exception: {str(e)}")
            return False

    def test_empty_quiz_attempt(self) -> bool:
        """Test submitting empty quiz attempt"""
        try:
            if not self.created_quiz_id:
                self.log_test("Empty Quiz Attempt", "FAIL", "No quiz ID available for testing")
                return False
            
            attempt_data = {
                "responses": [],
                "time_taken": 60
            }
            
            response = self.session.post(
                f"{self.base_url}/quizzes/{self.created_quiz_id}/attempt",
                json=attempt_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Should handle empty responses gracefully
                if result["score"] == 0 and result["percentage"] == 0.0:
                    self.log_test("Empty Quiz Attempt", "PASS", "Empty attempt handled correctly")
                    return True
                else:
                    self.log_test("Empty Quiz Attempt", "FAIL", "Empty attempt scoring incorrect")
                    return False
            else:
                self.log_test("Empty Quiz Attempt", "FAIL", f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Empty Quiz Attempt", "FAIL", f"Exception: {str(e)}")
            return False

    def run_all_tests(self) -> Dict[str, bool]:
        """Run all backend API tests"""
        print("=" * 60)
        print("MINI QUIZ PLATFORM - BACKEND API TESTING")
        print("=" * 60)
        print(f"Testing API at: {self.base_url}")
        print()
        
        test_results = {}
        
        # Core API Tests
        test_results["health_check"] = self.test_health_check()
        test_results["create_quiz"] = self.test_create_quiz()
        test_results["list_quizzes"] = self.test_list_quizzes()
        test_results["get_quiz_for_taking"] = self.test_get_quiz_for_taking()
        test_results["submit_quiz_attempt"] = self.test_submit_quiz_attempt()
        test_results["get_quiz_result"] = self.test_get_quiz_result()
        test_results["get_all_results_admin"] = self.test_get_all_results_admin()
        
        # Edge Case Tests
        test_results["invalid_quiz_retrieval"] = self.test_invalid_quiz_retrieval()
        test_results["empty_quiz_attempt"] = self.test_empty_quiz_attempt()
        
        # Summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in test_results.values() if result)
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "PASS" if result else "FAIL"
            symbol = "✅" if result else "❌"
            print(f"{symbol} {test_name.replace('_', ' ').title()}: {status}")
        
        print()
        print(f"Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All backend API tests PASSED!")
        else:
            print(f"⚠️  {total - passed} test(s) FAILED")
        
        return test_results

if __name__ == "__main__":
    tester = QuizPlatformTester()
    results = tester.run_all_tests()