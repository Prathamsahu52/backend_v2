# backend
CampusPay backend

(Make sure you have Python 3.8 or above and latest version of pip installed on your system before starting this setup.)

For the developing team:
Clone the branch titled with <your-name> into your required directory.
  
For everyone else:
Clone the main branch into your required directory.

1. **Setting up and activating the virtual environment**
  a) For Windows: 
     py -m pip install --user virtualenv (this downloads the packages necessary for creating virtual environments on your system)
     py -m venv djangoenv (this creates a virtual environment)
     djangoenv\Scripts\activate.bat (this activates your virtual environment)
     
     
  b) For Linux/MacOS:
     python3 -m pip install --user virtualenv
     python3 -m venv djangoenv
     source djangoenv/bin/activate

You may now navigate to the directory containing your backend repository using the terminal. Now you can run the following command:
  a) For Windows/Linux/MacOS:
     pip install -r requirements.txt
     pip freeze > requirements.txt
  
This installs all the requirements in the requirements.txt file and freezes them to prevent updates.
If you wish, you can install all the required packages step-by-step as well.
  
2. **Install Django version 4.1.7**
  a) For Windows: 
     pip install django==4.1.7
  b) For Linux/MacOS: 
     pip3 install django==4.1.7
  
  
3. **Install djangorestframework version 3.14.0**
  a) For Windows:
     pip install djangorestframework==3.14.0
  b) For Linux/MacOS:
     pip3 install djangorestframework==3.14.0
     
4. **Install django-cors-headers version 3.13.0**
  a) For Windows:
     pip install django-cors-headers==3.13.0
  b) For Linux/MacOS:
     pip3 install django-cors-headers=3.13.0
  
5. **Install djangorestframework-simplejwt version 5.2.2**
  a) For Windows:
     pip install djangorestframework-simplejwt==5.2.2\
  b) For Linux/MacOS:
     pip3 install djangorestframework-simplejwt==5.2.2
  
You are now good to go!
