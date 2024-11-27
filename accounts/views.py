from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView
from accounts.models import CustomUser
from django.contrib.auth import login, logout


# Index page view
class IndexView(TemplateView):
    template_name = 'index.html'


# To show landing page
class LandingPageView(TemplateView):
    template_name = 'landing_page.html'
    
    
# Signup page view    
class SignupView(TemplateView):
    template_name ='signUp.html'
    
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        country = request.POST.get('country')
        country_code = request.POST.get('country_code')
        
        errors = {'email':None, 'mobile':None, 'confirm_password':None}
        
        if not mobile.isdigit():
            errors['mobile'] = "Mobile number must contain only digits"
            
        if new_password != confirm_password:
            errors['confirm_password'] = "Passwords do not match"

        if CustomUser.objects.filter(email=email).exists():
            errors['email'] = "Email is already registered"
        
        if CustomUser.objects.filter(mobile=mobile).exists():
            errors['mobile'] = "Mobile number is already registered"
                
        if any(errors.values()):
            return render(request, self.template_name, {'errors': errors, 'name': name, 'email': email, 'mobile': mobile})
        
        user = CustomUser(name=name, email=email, mobile=mobile, country=country, countryCode=country_code)
        user.set_password(new_password)
        user.save()
        
        return redirect('index')
    
    
# Login View
class SignInView(TemplateView):
    template_name = 'signIn.html'
    
    def post(self, request, *args, **kwargs):
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        errors = {'mobile':None, 'password':None}
        
        user = CustomUser.objects.filter(mobile=mobile).first()
        
        if not user:
            errors['mobile'] = "User with this mobile number is not registered"
        elif not user.check_password(password):
            errors['password'] = "Password is incorrect"

        if any(errors.values()):
            return render(request, self.template_name, {'errors': errors, 'mobile': mobile})
        
        login(request, user)
        if user.user_type == 'Doctor':
            return redirect('doctor_home')
        else:
            return redirect('home')
    
    
#Logout View
class SignOutView(View):
    def post(self, request, *args, **kwargs):
        logout(request) 
        return redirect('index')  
        
        
