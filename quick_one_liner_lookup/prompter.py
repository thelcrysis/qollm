import glob
import os
from pathlib import Path
import re
import time
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from quick_one_liner_lookup.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from quick_one_liner_lookup.settings import (
    CLOUD_MODEL,
    LOCAL_MODEL,
    OLLAMA_BASE_URL,
    check_use_cloud,
    check_use_rag,
    is_debug_mode_active,
)
from quick_one_liner_lookup.utils import create_open_ai_instance

db_name = "vector_db"


def postprocessing(command: str) -> str:
    REGEX_PATTERN = r"(```|`)?(bash\n)?(?P<command>[^`]*)(```|`)?"

    command = command.strip()
    regex = re.compile(REGEX_PATTERN, re.DOTALL)
    matches = list(regex.finditer(command))
    if not matches:
        return command.strip()

    for m in matches:
        cmd = m.groupdict().get("command")
        if cmd:
            return cmd.strip()

    return command


def prompt(
    command_description: str,
    log: bool = True,
) -> str:
    open_ai = create_open_ai_instance()
    user_prompt = USER_PROMPT_TEMPLATE.format(command_description)

    system_prompt = SYSTEM_PROMPT
    if check_use_rag():
        # embeddings = HuggingFaceEmbeddings(model_name="multilingual-e5-large-instruct")
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        if os.path.exists(db_name):
            vectorstore = Chroma(persist_directory=db_name, embedding_function=embeddings)
        else:
            documents = []
            loader = DirectoryLoader(
                "./knowledge",
                glob="*.txt",
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"},
            )
            folder_docs = loader.load()
            for doc in folder_docs:
                doc_type = doc.metadata["source"].split("knowledge/")[1].split("_")[0]
                doc.metadata["doc_type"] = doc_type
                documents.append(doc)

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=300)
            chunks = text_splitter.split_documents(documents)
            vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=db_name)
        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.25, "k": 5},
        )
        system_prompt = f"{SYSTEM_PROMPT}\n\n Here is some context which might be relevant (disregard if it doesn't seem helpful):\n{retriever.invoke(command_description)}"

    if not check_use_cloud():
        response = open_ai.chat.completions.create(
            model=LOCAL_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    else:
        response = open_ai.chat.completions.create(
            model=CLOUD_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            reasoning_effort="low",
        )

    raw_command = response.choices[0].message.content

    if is_debug_mode_active():
        print(raw_command)

    command = postprocessing(raw_command)

    # Log description result pairs
    if log:
        log_file = Path(__file__).parent / "prompt_answer_pairs.csv"
        with open(log_file, "a") as f:
            f.write(f"\n{command_description},{command}")

    return command


if __name__ == "__main__":
    print(prompt("give me weather for zagreb"))
