#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

# IMPORT VARI E DEFINIZIONE DELLE VERSIONI PER BOT TELEGRAM
import logging
import random
import os
import pickle
import AIDAkeys
import langchain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain import PromptTemplate
from langchain.memory import  ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType

from telegram import __version__ as TG_VER


try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Percorso del file JSON delle credenziali
cred = credentials.Certificate(AIDAkeys.firebaseCertificate)

# Inizializza l'app Firebase
firebase_admin.initialize_app(cred,{
    'databaseURL': AIDAkeys.databaseURL
})


######### Definizione di chiavi, persist directory e vectorDB (ChromaDB)

os.environ['OPENAI_API_KEY'] = AIDAkeys.openAIkeyAndrea
embeddings = OpenAIEmbeddings()
persist_directory = 'ChromaDB_Bicocca_AIDA_FINAL'
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

######### Creazione di prompt per la conversazione
prompt=ChatPromptTemplate(
    input_variables=['context', 'question'], 
    output_parser=None,
    partial_variables={}, 
    messages=[
        SystemMessagePromptTemplate(
            prompt = PromptTemplate(
                input_variables=['context'], 
                output_parser=None, 
                partial_variables={}, 
                template=AIDAkeys.template, 
                template_format='f-string', 
                validate_template=True), 
                additional_kwargs={}), 
                HumanMessagePromptTemplate(
                    prompt = PromptTemplate(
                        input_variables=['question'], 
                        output_parser=None, 
                        partial_variables={}, 
                        template='{question}', 
                        template_format='f-string', 
                        validate_template=True), 
                        additional_kwargs={})])

######## Funzione processThought: semplice passaggio che restituisce ciò che gli viene passato come argomento
def processThought(thought):
  return thought
 
#langchain.debug = True



####### Configurazione del sistema di logging del bot
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


####### Definizione di un gestore di comando (start)

####### Questa funzione è un gestore di comando per il comando /start. 
# Quando un utente avvia il bot usando il comando /start, questa funzione viene chiamata. 
# Riceve due argomenti: update e context.
# 
# * update: Contiene le informazioni sull'aggiornamento ricevuto, ad esempio il messaggio, l'utente, ecc.
# * context: Contiene il contesto dell'aggiornamento.
# 
# All'interno della funzione, viene estratto l'utente che ha inviato l'aggiornamento.
# Successivamente, viene controllato se esiste già una memoria associata a quell'utente nell'archivio Firebase.
# 
# Se la memoria esiste, viene inviato un messaggio di benvenuto abbreviato. 
# Se la memoria non esiste, viene creata una nuova ConversationBufferWindowMemory, serializzata e salvata nell'archivio Firebase. 
# Viene quindi inviato un messaggio di benvenuto più lungo che presenta il bot AIDA e le sue capacità.

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user

    ref_mem = db.reference('/chats/'+str(user.id)+'/memory/')
    snapshot_mem = ref_mem.get()

    

    if snapshot_mem is not None :
        await update.message.reply_html(
            f"""Ciao {user.first_name}!
Come posso aiutarti?
        """,          
        )

    else:

        chat_mem = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k = 5)
        
   
        ref_mem.set(pickle.dumps(chat_mem).hex())
        

        await update.message.reply_html(
            rf"""Ciao {user.mention_html()}!
Ciao! Sono AIDA, la tua assistente virtuale specializzata nell'orientamento tra le offerte formative dell'Università degli Studi di Milano-Bicocca. 
Che tu abbia finito le scuole superiori o che tu abbia finito una laurea triennale, sono ciò che fa per te!

Sono qui per fornirti informazioni, risposte e supporto e per aiutarti nella tua scelta tra diversi corsi di laurea triennale e/o magistrale. 
Hai domande tecniche, necessità di consigli o curiosità legate ai tuoi interessi? Non esitare a chiedermi tutto ciò di cui hai bisogno. 

Ad esempio, sei interessato al machine learning? Fammi una domanda come questa: “Mi piace studiare machine learning e voglio scoprire di più in questo ambito, ci sono corsi che mi consiglieresti?”.
Oppure, ancora: “Mi piacerebbe diventare un financial manager, vorrei acquisire competenze manageriali, informatiche e di relazione con il cliente. Quale corso di laurea triennale potrei seguire?".

Sono programmata, proprio come un esperto del settore, per offrire risposte rapide, accurate e personalizzate relative ai corsi erogati dall'Università Bicocca. 
Sono entusiasta di collaborare con te e di rendere la tua esperienza di orientamento universitario ancora più piacevole e soddisfacente.
 
Non vedo l'ora di aiutarti! Benvenuto a bordo!

DISCLAIMER:
Il bot è ancora in fase di sviluppo: potrebbe fornire delle informazioni non totalmente corrette o inventate.
Potrebbe dare nomi di corsi di laurea che non sono presenti in Bicocca e potrebbe confondere i corsi di laurea con gli insegnamenti (corsi di studio).

Puoi utilizzare /reset se hai bisogno di cancellare la mia memoria.""",
            
        )


####### Questa funzione viene chiamata quando l'utente invia il comando /reset. Questa funzione esegue le seguenti azioni:
# 
# * Prende l'utente che ha inviato l'aggiornamento.
# * Ottiene un riferimento al nodo della memoria dell'utente nell'archivio Firebase.
# * Crea una nuova ConversationBufferWindowMemory.
# * Serializza la nuova memoria e la salva nell'archivio Firebase.
# * Invia un'emoji di espressione sorpresa 😵‍💫 e un messaggio indicando che la memoria è stata cancellata.

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user = update.effective_user
    ref_mem = db.reference('/chats/'+str(user.id)+'/memory/')
    

    chat_mem = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k = 5)
    
    
    ref_mem.set(pickle.dumps(chat_mem).hex())
    


    await update.message.reply_text("😵‍💫")
    await update.message.reply_text("Possiamo parlare di un altro argomento, mi sono dimenticata di tutto ciò che mi hai detto.")



####### Questa funzione viene chiamata quando l'utente invia un messaggio di testo. Esegue le seguenti azioni:
# 
# * Prende l'utente che ha inviato il messaggio e l'ID della chat.
# * Invia casualmente un'emoji di attesa tra un elenco di emoji definite in waitingEmoji.
# * Ottiene un riferimento alla memoria dell'utente nell'archivio Firebase.
# * Carica la memoria serializzata e la converte in un oggetto di tipo ConversationBufferWindowMemory.
# * Configura Conversational retrieval chain (qa) utilizzando l'agente ChatOpenAI, il recupero dal database di vettori e la memoria.
# * Configura un altro agente di tipo ChatOpenAI (llm) per ulteriori operazioni.
# * Definisce una lista di strumenti (tools) che l'agente può utilizzare, incluso il "Bicocca QA System" e il "Thought Processing".
# * Inizializza l'agente con i tool definiti.
# * Imposta il template del prompt dell'agente.
# * Esegue l'agente con l'input del messaggio dell'utente e ottiene una risposta.
# * Aggiorna la memoria nell'archivio Firebase con la nuova memoria dell'agente.
# * Cerca di cancellare il messaggio precedente dell'utente (potrebbe generare un'eccezione se non riesce).
# * Invia la risposta dell'agente come messaggio.


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    # Ottieni l'utente che ha inviato il messaggio e l'ID della chat
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Lista di emoji che indicano all'utente che il bot sta elaborando la richiesta
    waitingEmoji = ["🤔", "💭", "🔎", "💬"]

    # Invia un messaggio all'utente con un'emoji scelta casualmente
    await update.message.reply_text(random.choice(waitingEmoji))

    # Ottieni un riferimento al nodo della memoria dell'utente nell'archivio Firebase
    ref_mem = db.reference('/chats/'+str(user.id)+'/memory/')
    # Ottieni lo snapshot della memoria attuale dell'utente
    snapshot_mem = ref_mem.get()
    # Deserializza e assegna la memoria
    memory = pickle.loads(bytes.fromhex(snapshot_mem))

    # Creazione di un oggetto ConversationalRetrievalChain che serve per rispondere alle domande poste dall'utente cercando i documenti con conenuto più simili alla domanda dell'utente all'interno del vectordb
    # la ricerca viene effettuata per similarità e vengono presi i 4 documenti più simili

    qa = ConversationalRetrievalChain.from_llm(ChatOpenAI(temperature=0, model_name=AIDAkeys.modelName),
                                           verbose=True,
                                           retriever=vectordb.as_retriever(search_type="similarity", search_kwargs={"k":4}),
                                           memory=memory,
                                           chain_type="stuff",
                                           condense_question_llm=ChatOpenAI(temperature=0, model_name=AIDAkeys.modelName), # condensa la domanda corrente e la chat history in una standalone question (necessario per creare un standalone vector per effettuare il retrieval)
                                           combine_docs_chain_kwargs={'prompt': prompt}
                                       )

    # Caricato il LLM che viene utilizzato per controllare l'agente
    llm = ChatOpenAI(temperature=0, model_name=AIDAkeys.modelName)

    # Definizione di una lista di strumenti

    # Il primo tool serve per rispondere a domande specifiche relative ai documenti, quindi viene utilizzato quando per rispondere alla domanda serve accedere al vectordb
    # Il secondo tool serve per rispondere a domande più generiche che non richiedono il retrieval di documenti, quindi domande a carattere più generico (es. Come ti chiami? oppure Ciao!)
    tools = [
        Tool(
            name="Bicocca QA System",
            func=qa.run,
            description="""useful for when you need to answer questions about courses at the University of Milano-Bicocca. It is useful when the user asks for suggestions and advices. It allows you to find information into document of degree programs or teachings belonging to a degree program.
            This tool is useful when the user asks for informations about University of Milano-Bicocca aspects. Input should be a question."""
        ),
        Tool(
            name="Thought Processing",
            description="""This is useful for when you have a thought that you want to use in a task,
            but you want to make sure it's formatted correctly.
            Input is your thought and self-critique and output is the processed thought.""",
            func=processThought,
        )
    ]

    # Inizializzazione dell'agente
    agent = initialize_agent(tools, # due tool da usare
                             llm, # LLM che guida e controlla l'agent
                             agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION, # scelto perchè è un agent ottimizzato per le conversazioni
                             verbose=True,
                             memory=memory,
                             agent_kwargs={
                                 "input_variables": ["input", "agent_scratchpad", "chat_history"], # Additional keyword arguments to pass to the underlying agent
                             },
                             handle_parsing_errors=True,
                             )

# we need an agent_scratchpad input variable to put notes on previous actions and observations.
# This should almost always be the final part of the prompt.
# This is a very important step, because without the agent_scratchpad the agent will have no context on the previous actions it has taken.


    # Stampa il testo del messaggio inviato dall'utente
    print(update.message.text)

    # Imposta il template del prompt dell'agente
    agent.agent.llm_chain.prompt.template = AIDAkeys.templateAgent

    # Esegue l'agente con l'input del messaggio e ottiene una risposta
    response = agent.run(input=str(update.message.text))

    # Serializza e salva la memoria dell'agente nell'archivio Firebase
    ref_mem.set(pickle.dumps(agent.memory).hex())

    # Ottieni l'ID del messaggio inviato dall'utente
    message_id = update.effective_message.message_id

    try:
        # Prova a cancellare il messaggio precedente dell'utente
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id+1)
    except:
        # Se non riesce, invia un messaggio di errore all'utente
        await update.message.reply_text("Si è verificato un errore riprova")
        return

    # Invia la risposta dell'agente come messaggio all'utente
    await update.message.reply_text(response)

    # Libera la memoria eliminando gli oggetti qa e agent
    del qa
    del agent


###### Questa funzione avvia l'applicazione del bot. 
# Crea un'istanza di Application, aggiunge gestori di comandi (CommandHandler) per i comandi /start e /reset, e un gestore di messaggi (MessageHandler) per gli altri messaggi di testo. 
# Infine, avvia il bot in modalità di ascolto.

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(AIDAkeys.telegramBOTtoken).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()




####### Questo blocco controlla se lo script è stato eseguito direttamente (non importato come modulo) e in tal caso, esegue la funzione main() per avviare il bot.

if __name__ == "__main__":
    main()