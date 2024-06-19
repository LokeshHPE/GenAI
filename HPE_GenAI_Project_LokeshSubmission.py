''' HPE Gen AI Project - Assessment Submission
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

================================================================================================================== '''

import os
import tempfile
import streamlit as st
import spacy
import fitz
import pandas as pd
import camelot
import re
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.indexes import VectorstoreIndexCreator

openai_api_key = os.getenv("OPENAI_API_KEY")       

def load_pdf_and_create_index(file_content):
    with tempfile.NamedTemporaryFile(delete=False, suffix="pdf") as temp_file_qa:
        temp_file_qa.write(file_content)
        temp_file_path_qa = temp_file_qa.name

    loader  = PyMuPDFLoader(temp_file_path_qa)
    pages   = loader.load_and_split()

    text_splitter       = CharacterTextSplitter(separator="\n", chunk_size=2000, chunk_overlap=200)
    texts               = text_splitter.split_documents(pages)
    index_creator       = VectorstoreIndexCreator()
    vectorstore_index   = index_creator.from_documents(texts).vectorstore

    return vectorstore_index

def extract_text_from_pdf(file_content):
    doc = fitz.open(stream=file_content, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def extract_company_name(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    company_names = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    return company_names

def contains_keywords(text, keywords):
    return any(keyword.lower() in text.lower() for keyword in keywords)

def extract_key_tables_from_pdf(file_content, keywords):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file_content)
        temp_file_path = temp_file.name

    if temp_file_path:
        try:          
            tables = camelot.read_pdf(temp_file_path, pages='all', flavor='stream')
            keyword_tables = []
            for table in tables:
                page = table.page
                table_bbox = table._bbox
                table_df = table.df
                
                # Extract text around the table
                doc = fitz.open(temp_file_path)
                page_text = doc[page - 1].get_text("text", clip=table_bbox)
                
                if contains_keywords(page_text, keywords):
                    keyword_tables.append(table_df)
            
            doc.close()
            return keyword_tables
        
        except Exception as e:
            st.error(f"An error occurred while reading key tables from PDF: {e}")
            return []
        
    else:
        st.error("Failed to save the uploaded PDF file.")
        return []

def extract_specific_dates(text):
    date_pattern = r'(for the (quarterly|fiscal) period ended:\s*(\w+\s\d{1,2},\s\d{4}))|(for the  fiscal year ended:\s*(\w+\s\d{1,2},\s\d{4}))'
    matches = re.findall(date_pattern, text.lower())
    
    # Extracting Financial Statement Period
    df_period = pd.DataFrame(matches)
    doc_period = df_period[0][0].title()        
    return doc_period
    
    
def main():
    st.title("Financial Statement Analysis of Form 10-K & 10-Q Reports")

    with st.sidebar:
        st.header("Basic Information:")
        st.write("1. Form 10-K is a Annual Report & Audited Financial Statements which is filed every Fiscal Year")
        st.write("2. Form 10-Q is a Quarterly Report & Unaudited Financial Statements filed every Fiscal Quarter")
        st.write("3. Both Forms are filed by Public Co. to US SEC about their Financial Performance")        
        st.write("----------------------------")     
        st.header("About Model:")
        st.write("As you upload Financial Statements, model identifies Company Name, Period Ending and extracts 3 important Financials i.e.,")
        st.write("i) Earnings Statement")
        st.write("ii) Balance Sheet")
        st.write("iii) Cash Flow Statement")
    
    pdf_file = st.file_uploader("Kindly upload PDF format of Financial Statements as shown in below example snapshot", type="pdf")

    if pdf_file is not None:
        try:
            file_content = pdf_file.read()
            
            # Extract text from the uploaded PDF file
            text = extract_text_from_pdf(file_content)
            
            st.write("========================================================================================")
            st.subheader("Key Points on Document Uploaded:")
            
            with st.expander("Company Name & Period Ending"):            
                # Calling UDF to Extract Company Name
                company_names = extract_company_name(text)            
                if company_names:
                    df = pd.DataFrame(company_names, columns=["Company Name"])
                    filtered_df = df[df["Company Name"].str.lower().str.contains("company|inc.|ltd|enterprise|corporation")]
                    first_company = filtered_df.iloc[0]["Company Name"] if not filtered_df.empty else "Unknown"
                    st.write(f" - {first_company.title()}")
                else:
                    st.write("No company names found in the document.")
    
                # Calling UDF to Extract Period Ending
                doc_period = extract_specific_dates(text)
                if doc_period:
                    st.write(f" - {doc_period}")
                else:
                    st.write("No specific dates found in the document.")

            with st.expander("Key Financial Statements"):                
                # Calling UDF to Extract Tables with specific keywords
                keywords = ["Earnings before provision for taxes", "total current assets", "total current liabilities",
                            "net cash provided by operating activities","net cash used in investing activities"]
                
                dataframes = extract_key_tables_from_pdf(file_content, keywords)
                
                # Assigning labels to Tables
                table_labels = ["Consolidated Statements of Earnings", "Consolidated Balance Sheets", "Consolidated Statements of Cash Flows"]
                if dataframes:
                    for i, df in enumerate(dataframes[:3]):
                        table_label = table_labels[i] if i < len(table_labels) else f"Table {i+1}"
                        st.subheader(table_label)
                        st.dataframe(df)
                else:
                    st.write("No tables matching the specified keywords extracted.")
        
            try:
                # Calling UDF - Language model and QA section
                vectorstore_index = load_pdf_and_create_index(file_content)
            
                llm = OpenAI(temperature=0.3)
            
                qa = RetrievalQA.from_chain_type(
                    llm=llm,
                    chain_type="stuff",
                    retriever=vectorstore_index.as_retriever(search_kwargs={"fetch_score": True}),
                    return_source_documents=True,
                )
            
                with st.expander("Q & A with uploaded Financial Statement"):
                    query = st.text_input("Ask a question about the financial report")
            
                    if query:
                        result = qa({"query": query})
                        st.write(f"Answer: {result['result']}")
                        st.write(f"Source Documents: {result['source_documents']}")                        
            except Exception as e:
                st.error(f"An error occurred while executing QA Section: {e}")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")        

    else:
        st.image("Financial_Statement_Format.PNG", caption='Example Document',
                 use_column_width=True, output_format="PNG")

if __name__ == "__main__":
    main()