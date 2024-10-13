from django.utils.decorators import method_decorator
from rest_framework.authtoken.models import Token
from django.http import JsonResponse
from rest_framework.views import APIView
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.response import Response
from rest_framework import status, views, response
from django.contrib import auth
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token
from school.models import User, School, Student, Teacher
from .serializers import UserSerializer, SchoolSerializer, TeacherSerializer, StudentSerializer

@method_decorator(ensure_csrf_cookie, name='dispatch')
class RegisterView(APIView):
    def post(self, request):
        print(request.data)
        role = request.data.get('role')
        user_data = request.data.get('user', {})
        email = user_data.get('email')
        username = user_data.get('username')
        password = user_data.get('password')

        print(f"Role: {role}, Email: {email}, Username: {username}, Password: {'*' * len(password)}")
        if role != 'school':
            print(f"School ID: {request.data.get('school')}, type: {type(request.data.get('school'))}")

        if not all([role, email, username, password]):
            missing = [field for field in ['role', 'email', 'username', 'password'] if not locals()[field]]
            return Response({'error': f'{", ".join(missing)} is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if role == 'school':
            if not all([request.data.get('full_name'), request.data.get('location')]):
                return Response({'error': 'full_name and location are required for schools.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if not all([request.data.get('first_name'), request.data.get('last_name'), request.data.get('school')]):
                return Response({'error': 'first_name, last_name, and school are required for non-schools.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer_for_role(role, request.data)
        if serializer.is_valid():
            user = self.create_user_with_role(role, serializer)
            auth_user = authenticate(username=user.username, password=request.data.get('user')['password'])
            print(f"Authenticating: username={user.username}, password={request.data.get('user')['password']}")
            print(f"auth_user: {auth_user}")
            if auth_user is not None:
                login(request, auth_user)
                print(f"Logged in user: {auth_user}")
                
                token, created = Token.objects.get_or_create(user=user)

                if role == 'school':
                    instance = School.objects.get(user=user)
                    user_serializer = SchoolSerializer(instance)
                elif role == 'teacher':
                    instance = Teacher.objects.get(user=user)
                    user_serializer = TeacherSerializer(instance)
                elif role == 'student':
                    instance = Student.objects.get(user=user)
                    user_serializer = StudentSerializer(instance)
                
                return Response({
                    'user': user_serializer.data, 
                    'role': role, 
                    'token': token.key
                }, status=status.HTTP_201_CREATED)
            else:
                print("Authentication failed")
                return Response({'error': 'Authentication failed.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create_user_with_role(self, role, serializer):
        print(f"Role: {role}") 
        print(f"Validated data: {serializer.validated_data}") 
        if role == 'school':
            school = serializer.save()
            user = school.user
        elif role == 'teacher':
            teacher = serializer.save()
            user = teacher.user
        elif role == 'student':
            student = serializer.save()
            user = student.user
        
        print(f"Created user: {user.username}, {user.email}, {serializer.validated_data['user']['password']}")
        return user

    def get_serializer_for_role(self, role, data):
        if role == 'school':
            return SchoolSerializer(data=data)
        elif role == 'teacher':
            return TeacherSerializer(data=data)
        elif role == 'student':
            return StudentSerializer(data=data)
        else:
            return None
    
@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            if user.is_school:
                role = 'school'
                instance = School.objects.get(user=user)
                serializer = SchoolSerializer(instance)
            elif user.is_teacher:
                role = 'teacher'
                instance = Teacher.objects.get(user=user)
                serializer = TeacherSerializer(instance)
            elif user.is_student:
                role = 'student'
                instance = Student.objects.get(user=user)
                serializer = StudentSerializer(instance)
            else:
                return Response({'error': 'User role not found.'}, status=status.HTTP_400_BAD_REQUEST)

            token, created = Token.objects.get_or_create(user=user)

            res = Response({
                'user': serializer.data, 
                'role': role, 
                'token': token.key
            }, status=status.HTTP_200_OK)
            res.set_cookie('userToken', token.key, httponly=False)

            return res
        else:
            return Response({'error': 'Invalid username or password.'}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFToken(views.APIView):
    def get(self, request, format=None):
        csrftoken = get_token(request)
        
        return response.Response({ 'csrftoken': csrftoken })
    
class LogoutView(views.APIView):
    def post(self, request, format=None):
        try:
            auth.logout(request)
            response = JsonResponse({"message": "You're logged out."})
            response.delete_cookie('csrftoken')
            return response
        except:
            return JsonResponse({ 'success' : 'Error while logging out'})
