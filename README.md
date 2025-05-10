# **ERP System Optimization & Development**  

### **About the Project**  
This project focuses on optimizing an in-house **ERP system (XLPlat)** by transitioning from **TCL** to **Django**, enhancing existing modules, and integrating new features like **Finance and BDM**. Additionally, functionalities such as **resume parsing, bill reimbursement, resignation management, attendance tracking, and email integration** have been implemented to streamline operations.  

---

## **Features**  
- **ERP Optimization**: Migrating and improving **TCL-based** modules using **Django**.  
- **Project Allocation**: Assigning and tracking projects within the system.  
- **Attendance Management**: Logging working hours and generating reports.  
- **Resignation Workflow**: Automating approval processes for resignations.  
- **Email Integration**: Sending and receiving emails directly through ERP.  
- **Calendar & Events**: Managing meetings, deadlines, and holidays.  
- **Resume Parser**: Extracting relevant information from resumes for HR processing.  
- **Bill Reimbursement**: Automating the approval and tracking of expense claims.  

---

## **Technology Stack**  
- **Backend**: Django, PostgreSQL  
- **Frontend**: HTML, Tailwind CSS  
- **Other**: TCL (Legacy System) 

---

## **Setup Instructions**  
1. Clone the repository:  
   ```sh
   git clone https://github.com/your-username/erp-system.git
   cd erp-system
   ```
2. Set up a virtual environment and install dependencies:  
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Apply database migrations:  
   ```sh
   python manage.py migrate
   ```
4. Create a superuser:  
   ```sh
   python manage.py createsuperuser
   ```
5. Run the development server:  
   ```sh
   python manage.py runserver
   ```
6. Access the ERP system at:  
   ```
   http://127.0.0.1:8000/
   ```

---

## **PPT & Video**  
[PPT]([https://github.com/aryam643/ERP_Training/blob/PPT_Video/G24C.pptx])


[Click here to watch the project demo](https://drive.google.com/file/d/1q1SPIwkiD1demq1jBRqfcxm3ilCAMiNu/view?usp=sharing)  

---

## **Contributors**  
- **Aryam Sharma** *(Software Product Developer Intern, TT Consultants)*  

---

## **License**  
This project is licensed under the **MIT License**.  
