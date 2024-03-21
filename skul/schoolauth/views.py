from django.utils.decorators import method_decorator
from rest_framework.authtoken.models import Token
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.decorators import api_view
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
        role = request.data.get('role')
        if role not in ['school', 'teacher', 'student']:
            return Response({'error': 'Invalid role.'}, status=status.HTTP_400_BAD_REQUEST)

        email = request.data.get('email')
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already in use.'}, status=status.HTTP_400_BAD_REQUEST)

        if role == 'school':
            serializer = SchoolSerializer(data=request.data)
        elif role == 'teacher':
            serializer = TeacherSerializer(data=request.data)
        elif role == 'student':
            serializer = StudentSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            if role == 'school':
                user.is_school = True
            elif role == 'teacher':
                user.is_teacher = True
            elif role == 'student':
                user.is_student = True
            user.save()

            auth_user = authenticate(username=user.username, password=request.data.get('user').get('password'))
            if auth_user is not None:
                login(request, auth_user)
            else:
                return Response({'error': 'Authentication failed.'}, status=status.HTTP_400_BAD_REQUEST)

            token, created = Token.objects.get_or_create(user=user)
            user_serializer = UserSerializer(user)

            res = Response({'user': user_serializer.data, 'token': token.key}, status=status.HTTP_201_CREATED)
            res.set_cookie('userToken', token.key, httponly=False)

            return res

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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
        return response.Response({ 'success': 'CSRF Cookie set'})
    
class LogoutView(views.APIView):
    def post(self, request, format=None):
        try:
            auth.logout(request)
            response = JsonResponse({"message": "You're logged out."})
            response.delete_cookie('csrftoken')
            return response
        except:
            return JsonResponse({ 'success' : 'Error while logging out'})
