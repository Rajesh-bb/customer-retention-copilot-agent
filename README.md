# 🤖 Customer Retention Copilot

<p align="center">

<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white"/>
<img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white"/>
<img src="https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white"/>
<img src="https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white"/>
<img src="https://img.shields.io/badge/Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white"/>
<img src="https://img.shields.io/badge/LangSmith-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white"/>
<img src="https://img.shields.io/badge/FAISS-FF6F00?style=for-the-badge&logo=meta&logoColor=white"/>

</p>

---

## 🎯 Objective

The **Customer Retention Copilot** is an **Agentic AI system for B2B SaaS Customer Success** designed to turn fragmented customer data into actionable retention decisions. It combines customer usage, support, billing, and engagement signals to identify at-risk accounts, understand **why** they are at risk, recommend **the best next action**, and execute approved interventions. The system reduces the manual effort required by Customer Success Managers while keeping humans in control of consequential actions. The goal is to transform customer retention from a **manual and reactive workflow** into a **proactive, AI-assisted decision and execution system**.

---

# 🚀 Approach

We built the system as a **multi-agent workflow** using **FastAPI, PostgreSQL, SQLAlchemy, LangChain/LangGraph, Gemini, Gmail, Google Calendar, Slack, LangSmith, and FAISS**.

Customer activity, usage, support, billing, and engagement data are analyzed to generate **customer health scores and risk categories**. The **Analyst Agent** investigates high-risk accounts using data from PostgreSQL and identifies the underlying root causes. The resulting customer analysis is passed to the **Recommendation Agent**, which selects one best retention action along with its priority and human-approval requirement. The **Action Agent** then prepares the required action, waits for human approval, and executes approved actions such as emails, meetings, and report generation.

A **CSM Agent** acts as the conversational orchestrator, routing user requests between:

* **Customer Analysis Tool** — generates a new analysis and report.
* **RAG Tool** — answers questions about an existing analysis.
* **Normal Conversation** — handles general questions without invoking tools.

We follow an **evaluation-driven development approach**, evaluating individual components independently rather than treating the entire system as a black box.

---

# 🧠 System Orchestration

The complete system is organized around the **CSM Agent and two main tools**.

```text
                           ┌──────────────┐
                           │     USER     │
                           └──────┬───────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │    CSM AGENT    │
                         │  Orchestrator   │
                         └────────┬────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
             New Analysis    Existing Report   General
                    │             │          Conversation
                    ▼             ▼
          ┌────────────────┐  ┌──────────────┐
          │ Analysis Tool  │  │   RAG Tool   │
          └───────┬────────┘  └──────┬───────┘
                  │                  │
                  │                  ▼
                  │             RAG Agent
                  │                  │
                  │                  ▼
                  │              Answer
                  │
                  ▼
          ┌────────────────┐
          │  Analyst Agent │
          └───────┬────────┘
                  │
                  │ SQLAlchemy
                  ▼
          ┌────────────────┐
          │  PostgreSQL DB │
          │ Customer Data  │
          └───────┬────────┘
                  │
                  ▼
          Customer Analysis
                  │
                  ▼
       ┌──────────────────────┐
       │ Recommendation Agent │
       └──────────┬───────────┘
                  │
                  ▼
          Best Next Action
                  │
                  ▼
          ┌────────────────┐
          │   Action Agent │
          └───────┬────────┘
                  │
                  ▼
          ┌────────────────┐
          │ Human Approval │
          └───────┬────────┘
                  │
             Approved?
              /       \
            No         Yes
            │           │
           END          ▼
                  ┌──────────────┐
                  │ Action       │
                  │ Execution    │
                  └──────┬───────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           Gmail      Calendar     Report
                         │
                         ▼
                       Slack
```

---

# 🔎 Customer Analysis Workflow

When the user requests a new analysis, the **Analysis Tool** starts the complete retention pipeline.

### 1. Analyst Agent

The Analyst Agent uses **SQLAlchemy** to query and analyze customer information stored in **PostgreSQL**.

The analysis combines signals such as:

```text
Usage Events
Support Tickets
Ticket Messages
Emails
Meetings
Billing Events
CSM Notes
Call Transcripts
        │
        ▼
   SQLAlchemy
        │
        ▼
 PostgreSQL
        │
        ▼
 Customer Analysis
```

The goal is to determine:

> **Which customers are at risk and why?**

---

### 2. Recommendation Agent

The customer analysis is passed to the Recommendation Agent.

```text
Customer Analysis
       ↓
Recommendation Agent
       ↓
Best Next Action
       ↓
Priority
       ↓
Human Approval Requirement
```

The agent selects one action from the available retention actions.

---

### 3. Vector Database

During the analysis workflow, the relevant analysis information is also prepared for semantic retrieval.

```text
Analysis Data
      ↓
Embeddings
      ↓
FAISS
      ↓
Retrievable Analysis Context
```

This enables the RAG tool to answer follow-up questions about previously generated analyses.

---

### 4. Action Agent

The Action Agent converts the recommendation into an executable workflow.

```text
Recommendation
      ↓
Prepare Payload
      ↓
Prepare Action Details
      ↓
Human Approval
      ↓
Execute Action
```

Approved actions can include:

* 📧 Sending customer emails
* 📅 Scheduling meetings
* 📄 Generating reports
* 💬 Sending information through Slack

---

### 5. Human Approval

Before consequential actions are executed:

```text
AI Recommendation
       ↓
Human Review
       ↓
 ┌─────┴─────┐
 │           │
Reject     Approve
 │           │
END          ▼
       Execute Action
```

This provides controlled automation while keeping the CSM responsible for the final decision.

LangGraph is particularly suited to this type of workflow because it provides low-level orchestration, persistence, streaming, and human-in-the-loop control.

---

# 🔍 RAG Workflow

The second CSM tool is the **RAG Tool**.

It is used when the user asks questions about an **existing customer analysis**.

```text
User Question
      ↓
    CSM Agent
      ↓
    RAG Tool
      ↓
   RAG Agent
      ↓
   Query FAISS
      ↓
Relevant Analysis
      ↓
     Gemini
      ↓
Grounded Answer
```

Example questions:

```text
"What were the main churn drivers?"

"Which accounts are high risk?"

"What recommendations were generated?"

"Which industry has the highest risk?"
```

The RAG workflow has an average latency of approximately **1.5 seconds**.

---

# ⚡ Reducing API Calls & Analysis Latency

A major optimization was required because the analysis workflow processes approximately **200 customer actions/events from the database**.

Sending each record separately to the Gemini API would create:

```text
200 records
   ↓
200 API calls
   ↓
High latency
   ↓
Higher API overhead
```

Instead, we implemented **prompt batching**.

```text
              ~200 Customer Records
                       │
                       ▼
                Prompt Batching
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
          Batch 1             Batch 2
             │                   │
             ▼                   ▼
          Gemini              Gemini
             │                   │
             └─────────┬─────────┘
                       ▼
                Combined Result
```

This significantly reduces the number of Gemini API calls required to analyze the complete customer dataset and improves the overall analysis pipeline.

---

# 📊 Evaluation & Impact

We evaluate the system **component by component** rather than treating the complete agent as a single black box.

## Tool Selection Evaluation

We created a **100-query evaluation dataset**:

| Expected Route          | Queries |
| ----------------------- | ------: |
| `run_customer_analysis` |      35 |
| `ask_about_analysis`    |      35 |
| `No Tool`               |      30 |
| **Total**               | **100** |

### Results

| Metric                           |     Result |
| -------------------------------- | ---------: |
| 🎯 Tool Selection Accuracy       |    **96%** |

The four errors were primarily difficult follow-up queries where distinguishing between **fresh analysis** and **questions about an existing analysis** was challenging.

---

## ⏱️ End-to-End Performance

| Workflow                      | Approx. Latency |
| ----------------------------- | --------------: |
| 🔬 Complete Customer Analysis |       **~95 s** |
| 🔍 RAG Follow-up              |      **~1.5 s** |

The ~95-second analysis latency includes the complete multi-agent workflow:

```text
Database Analysis
      ↓
Analyst Agent
      ↓
Recommendation Agent
      ↓
Vector DB Preparation
      ↓
Action Preparation
      ↓
Human Approval
      ↓
Action Execution
      ↓
Report Generation
```

---

# 💥 Impact

The system reduces the manual effort required to:

* Inspect fragmented customer data
* Identify risky accounts
* Understand **why** customers are at risk
* Decide **what to do next**
* Prepare customer interventions
* Schedule meetings
* Generate reports

The traditional CSM workflow:

```text
Find → Analyze → Decide → Execute
```

becomes:

```text
Review → Approve → Act
```

The key impact is therefore not simply **churn prediction**.

The system connects:

> **Customer Intelligence → Decision Making → Controlled Action**

while keeping human oversight for consequential actions.

---

# 🛠️ Tech Stack

<p align="center">

<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
<img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white"/>
<img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white"/>
<img src="https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white"/>
<img src="https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white"/>
<img src="https://img.shields.io/badge/Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white"/>
<img src="https://img.shields.io/badge/LangSmith-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white"/>
<img src="https://img.shields.io/badge/FAISS-FF6F00?style=for-the-badge&logo=meta&logoColor=white"/>

</p>

| Technology     | Purpose                                |
| -------------- | -------------------------------------- |
| **Python**     | Core application and agent development |
| **FastAPI**    | Backend API                            |
| **SQLAlchemy** | Database interaction and ORM           |
| **PostgreSQL** | Customer and event data                |
| **LangChain**  | LLM and tool integration               |
| **LangGraph**  | Multi-agent workflow orchestration     |
| **Gemini API** | LLM reasoning and analysis             |
| **FAISS**      | Vector database and semantic retrieval |
| **LangSmith**  | Tracing, monitoring and evaluation     |

LangChain provides the model/tool and agent abstractions, while LangGraph provides the lower-level orchestration needed for stateful workflows and controlled execution. LangSmith is used for tracing and evaluation of agent behavior.

