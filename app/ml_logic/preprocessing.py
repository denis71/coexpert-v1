import streamlit as st

from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from app.params import *

import pickle

import time


def load_pdf():
    '''Load pdf files from source folder'''
    print(f'Loading pages from {PDF_PATH_FILES}')
    loader = PyPDFDirectoryLoader(PDF_PATH_FILES)
    pages = loader.load()
    print(f'Loaded {len(pages)} pages')
    return pages


def split_pdf(pages):
    '''Preprocess pdf files'''
    # split the pages in small chunks
    # Change the chunk_size and chunk_overlap as needed
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=100)
    all_splits = text_splitter.split_documents(pages)
    print(f"Created {len(all_splits)} splits")

    with open(CACHE_PATH_SPLITS, "wb") as f:
        pickle.dump(all_splits, f)
        print(f'Saved all splits to cache folder: {CACHE_PATH_SPLITS}')

    return all_splits


def load_all_splits_cache():
    '''Load the all splits from cache'''
    try:
        with open(CACHE_PATH_SPLITS, "rb") as f:
            all_splits = pickle.load(f)
            print(f'Loaded from cache: {len(all_splits)} splits')
            return all_splits
    except FileNotFoundError:
        pages = load_pdf()
        all_splits = split_pdf(pages)
        return all_splits


def create_embeddings():
    '''Create the embeddings'''
    embeddings = OpenAIEmbeddings(
        openai_api_key=st.session_state["OPENAI_API_KEY"])
    print(f'Created embeddings')
    return embeddings


def create_retriever(all_splits, embeddings):
    '''Create the retriever'''
    retriever = Chroma.from_documents(
        all_splits, embeddings, persist_directory=CACHE_PATH_CHROMA).as_retriever()
    print(f'Created retriever: {retriever}')
    return retriever


def load_retriever(start_time):
    '''Load the retriever from cache'''
    embeddings = create_embeddings()
    try:
        retriever = Chroma(persist_directory=CACHE_PATH_CHROMA,
                           embedding_function=embeddings).as_retriever()
        print(f'Loaded from cache: {retriever}')
        return retriever
    except FileNotFoundError:
        preprocess_pdf_to_retriever(start_time)


def preprocess_pdf_to_retriever(start_time):
    '''Preprocess pdf files to retriever'''
    print("---------- %s seconds ----------" % (time.time() - start_time))
    if not os.path.exists(CACHE_PATH_SPLITS):
        print("No pdf splits found. Loading pdf and creating splits...")
        pages = load_pdf()
        print("---------- %s seconds ----------" % (time.time() - start_time))
        all_splits = split_pdf(pages)
        print("---------- %s seconds ----------" % (time.time() - start_time))
    else:
        print("Pdf splits found. Loading splits...")
        all_splits = load_all_splits_cache()
        print("---------- %s seconds ----------" % (time.time() - start_time))

    embeddings = create_embeddings()
    print("---------- %s seconds ----------" % (time.time() - start_time))
    retriever = create_retriever(all_splits, embeddings)
    print("---------- %s seconds ----------" % (time.time() - start_time))
    return retriever
