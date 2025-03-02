from fastapi import FastAPI
from dotenv import load_dotenv
from camel.agents import ChatAgent, CriticAgent
from camel.societies.workforce import Workforce
from camel.societies.role_playing import RolePlaying
from camel.tasks import Task
from colorama import Fore
from camel.utils import print_text_animated

load_dotenv()

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/chat/{message}")
def chat(message: str):
    # Create a chat agent with a system message
    agent = ChatAgent(system_message="You are a helpful assistant.")
    print(message)
    # Step through a conversation
    response = agent.step(message)
    return {"response": response.msgs[0].content}


@app.get("/workforce/{message}")
def workforce(message: str):
    # Create a chat agent with a system message
    professor = ChatAgent(
        system_message="You are a mathematics expert who explains formulas, proofs, and statistical concepts clearly."
    )
    note_taker = ChatAgent(
        system_message="You are an expert note-taker who organizes information clearly with bullet points, headings, and concise language."
    )
    summarizer = ChatAgent(
        system_message="You are a summarization expert. Create concise summaries that capture key points and maintain important details."
    )
    critic = CriticAgent(
        system_message="You are an academic critic with high standards for clarity, accuracy, and completeness. Evaluate content for logical gaps, unclear explanations, factual errors, and areas that need improvement. Provide specific, constructive feedback on how to enhance the material while maintaining a balanced perspective that acknowledges strengths alongside suggestions for improvement."
    )

    print(message)
    workforce = Workforce("Academic Note-Taking Workforce")
    workforce.add_single_agent_worker(
        "a mathematics expert",
        worker=professor,
    )
    workforce.add_single_agent_worker(
        "Expert note-taker",
        worker=note_taker,
    )
    workforce.add_single_agent_worker(
        "Summarization expert",
        worker=summarizer,
    )
    workforce.add_single_agent_worker("Academic Critic", worker=critic)

    task = Task(
        content="Create very detailed, exhaustive and comprehensive calculus 1 notes to prepare for the final exam. Don't include integrals.",
        id="0",
    )

    task = workforce.process_task(task)

    print(task.result)
    return {"response": task.result}


@app.get("/roleplay/{message}")
def roleplay(message: str):
    task_prompt = "Create very detailed, exhaustive and comprehensive calculus 1 notes to prepare for the final exam. Don't include integrals."

    critic_agent = CriticAgent(
        system_message="You are an academic critic with high standards. Review content for accuracy, clarity, and completeness. Provide specific improvement suggestions."
    )

    role_play_session = RolePlaying(
        assistant_role_name="University Professor",
        user_role_name="Student",
        task_prompt=task_prompt,
        with_critic_in_the_loop=True,
        with_task_specify=True,
        with_task_planner=True,
    )

    # Output initial message with different colors.
    print(
        Fore.GREEN
        + f"AI Assistant sys message:\n{role_play_session.assistant_sys_msg}\n"
    )
    print(Fore.BLUE + f"AI User sys message:\n{role_play_session.user_sys_msg}\n")
    print(Fore.MAGENTA + f"Critic sys message:\n{role_play_session.critic_sys_msg}\n")

    print(Fore.YELLOW + f"Original task prompt:\n{task_prompt}\n")
    print(
        Fore.CYAN
        + "Specified task prompt:"
        + f"\n{role_play_session.specified_task_prompt}\n"
    )
    print(Fore.RED + f"Final task prompt:\n{role_play_session.task_prompt}\n")

    n = 0
    input_msg = role_play_session.init_chat()

    # Output response step by step with different colors.
    # Keep output until detect the terminate content or reach the loop limit.
    chat_turn_limit = 5
    while n < chat_turn_limit:
        n += 1
        assistant_response, user_response = role_play_session.step(input_msg)

        if assistant_response.terminated:
            print(
                Fore.GREEN
                + (
                    "AI Assistant terminated. Reason: "
                    f"{assistant_response.info['termination_reasons']}."
                )
            )
            break
        if user_response.terminated:
            print(
                Fore.GREEN
                + (
                    "AI User terminated. "
                    f"Reason: {user_response.info['termination_reasons']}."
                )
            )
            break

        print_text_animated(Fore.BLUE + f"AI User:\n\n{user_response.msg.content}\n")
        print_text_animated(
            Fore.GREEN + "AI Assistant:\n\n" f"{assistant_response.msg.content}\n"
        )
        # print_text_animated(
        #     Fore.MAGENTA + "AI Critic:\n\n" f"{cri}\n"
        # )

        if "CAMEL_TASK_DONE" in user_response.msg.content:
            break

        input_msg = assistant_response.msg

    # very long and very detailed conversation but sooo many requests, i never got to the end. TODO.
    return {"response": input_msg}
