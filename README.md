# Breast-Cancer-Grading
Web based AI Grading for Breast Cancer IHC Markers

To find:
(1.) Mitotic cell detection on H&E images
(2.) Cell Detection on IHC Endometrium images
(3.) Breast Cancer cell classification on patches obtained from a WSI


https://github.com/NidhiTornekar/Breast-Cancer-Grading/assets/121748841/c3b32dd5-a161-4ad4-aad4-2a866365c8bc


Datasets Used : EndoNuke(for Endometrium Cell Detection), Miccai 2015(for Mitotic Cell Detection) and IHC Breast WSI
Model : YOLOv5


TO RUN:

Create .env file containing the following credentails:
KEY= enter a random key unique to you
DATABASE= enter your MongoDB Atlas URL
TWILIO_ACCOUNT_SID= enter Twilio Account ID
TWILIO_AUTH_TOKEN= enter Twilio Authentication Token
TWILIO_PHONE_NUMBER= enter Twilio Phone Number

Create a static folder containing Ground truth values(for Mitosis, EndoNuke images), obtained from the labels.

Train YOLOv5 models on Mitosis and EndoNuke datasets after required pre-processing(split, augment, etc) and add the corresponding best.pt files to the root directory of the project.

Run using the command python app.py and view results in localhost:5000

Can deploy using AWS.
