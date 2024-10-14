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
from .serializers import SchoolSerializer, TeacherSerializer, StudentSerializer

@method_decorator(ensure_csrf_cookie, name='dispatch')
class RegisterView(APIView):
    def post(self, request):
        role = request.data.get('role')
        if role not in ['school', 'teacher', 'student']:
            return Response({'error': 'Invalid role.'}, status=status.HTTP_400_BAD_REQUEST)

        email = request.data.get('user', {}).get('email')
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already in use.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer_for_role(role, request.data)
        if serializer.is_valid():
            instance = self.create_user_with_role(role, serializer)
            user = instance.user  # Get the user from the created instance

            # Debug print
            print(f"User created: {user.username}, {user.email}, is_active: {user.is_active}")

            # Ensure the password is set correctly
            user.set_password(request.data['user']['password'])
            user.save()

            # Debug print
            print(f"Password set for user: {user.username}")

            auth_user = authenticate(request, username=user.username, password=request.data['user']['password'])
            if auth_user is not None:
                login(request, auth_user)
                print(f"User authenticated: {auth_user.username}")
            else:
                print(f"Authentication failed for user: {user.username}")
                # Check if the user can be fetched from the database
                try:
                    user_check = User.objects.get(username=user.username)
                    print(f"User exists in DB: {user_check.username}, is_active: {user_check.is_active}")
                except User.DoesNotExist:
                    print(f"User does not exist in DB: {user.username}")
                return Response({'error': 'Authentication failed.'}, status=status.HTTP_400_BAD_REQUEST)

            token, created = Token.objects.get_or_create(user=user)
            
            if role == 'school':
                user_serializer = SchoolSerializer(instance)
            elif role == 'teacher':
                user_serializer = TeacherSerializer(instance)
            elif role == 'student':
                user_serializer = StudentSerializer(instance)
            
            res = Response({
                'user': user_serializer.data, 
                'role': role, 
                'token': token.key
            }, status=status.HTTP_201_CREATED)
            res.set_cookie('userToken', token.key, httponly=False)
            return res
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_for_role(self, role, data):
        if role == 'school':
            return SchoolSerializer(data=data)
        elif role == 'teacher':
            return TeacherSerializer(data=data)
        elif role == 'student':
            return StudentSerializer(data=data)

    def create_user_with_role(self, role, serializer):
        instance = serializer.save()
        user = instance.user
        
        if role == 'school':
            user.is_school = True
        elif role == 'teacher':
            user.is_teacher = True
        elif role == 'student':
            user.is_student = True
        
        user.save()
        return instance

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