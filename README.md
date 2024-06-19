# GenAI
Gen AI Project - Assessment Submission
------------------------------------------------------------------------------------------------------------------
Project     : Automated Financial Statement Analysis
Objective   : Build a tool to automate the analysis of financial statements for compliance with regulatory standards
------------------------------------------------------------------------------------------------------------------
About Project:
1. Financial Statement Analysis of Form 10-K & 10-Q Reports
2. Form 10-K is a Annual Report & Form 10-Q is a Quarterly Report
3. For project code execution, provided HPE Form 10-Q pdf document available to General Public
4. Used Streamlit to extract below information on upload of pdf document without QA
   i)   Company Name
   ii)  Period Ending
   iii) Key Financial Statements
        - Earnings Statement
        - Balance Sheet
        - Cash Flow Statement
5. Other Packages
   a) Used spacy & fitz from PyMuPDF for extracting texts
   b) Used camelot for extracting tables
   c) Used RetrievalQA for question answersing tasks
   d) Used VectorstoreIndexCreator to convert docuemnts & retrieval of information
