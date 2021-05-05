# ECE4564_FinalProject
This github contains our code for our final project for ECE 4564 in Spring 2021.

Our project/system provides a website along with tools that the government uses and tools that businesses will have.

Our website has three main pages:
1) Landing page - This page gives simple COVID statistics for the US, along with the number of people that our system has vacccinated. It also provides buttons to take the web visitor to the other pages of our website. (/today, /individual, and other websites that help give info on where vaccinations can be obtained)
2) Today page - This page gives more in depth COVID statistics regarding up-to-date current statistic in the US. It first provides a summary of the Top 10 states in the US based on the most active cases and the most new cases (new cases today). Also, it provides a dropdown to see the number of new cases and active cases in specific states. 
3) QR page - This page allows web visitors to input their information and get their unique QR code that will allow them to prove their vaccination status to businesses.

In addition, we have implemented the following government / business tools:
Government tool:
A tool that allows operators to add vaccination patient data to the database. The tool uses a GUI where their First Name, Middle Name, Last Name, DOB, and SSN are entered and they are entered into the database. Also, there is error checking to ensure the right input formats are used. 
Business tool:
This tool will be provided to businesses so that they can confirm that individuals are indeed vaccinated. The tool has a simple GUI that keeps track of the number of people that have been admitted to their establishment. It also uses the machines camera to scan and decode QR codes, send them to the government for verification, and report the results. The GUI flashes a color on the screen (green = permitted, yellow = possible duplicate QR code, red = invalid QR) and announces verbally if the individual is permitted access to the establishment. 

Notes:
Duplicate QR codes are protected against by keeping track of the number of times a business has scanned the QR code and ensuring that each QR can only be used for business access once. 
All data on the MongoDB database is encrypted so that no personal information is given to those who don't have access or hacked. (There is a development collection in our video that will be used to help us test, it would be removed before this system is deployed into the world). 
