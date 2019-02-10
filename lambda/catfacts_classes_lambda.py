import os

from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
import ask_sdk_dynamodb
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler, \
    AbstractRequestInterceptor, AbstractResponseInterceptor

skill_persistence_table = os.environ["skill_persistence_table"]

SKILL_NAME = 'Cat Facts'
sb = StandardSkillBuilder(
    table_name=skill_persistence_table, auto_create_table=False,
    partition_keygen=ask_sdk_dynamodb.partition_keygen.user_id_partition_keygen)

cat_facts = [
"A cat usually has about 12 whiskers on each side of its face.",
"On average, cats spend 2/3 of every day sleeping. That means a nine-year-old cat has been awake for only three years of its life.",
"In the original Italian version of Cinderella, the benevolent fairy godmother figure was a cat.",
"In the 1750s, Europeans introduced cats into the Americas to control pests.",
"Cats spend nearly 1/3 of their waking hours cleaning themselves.",
"A female cat is called a queen or a molly.",
"Rome has more homeless cats per square mile than any other city in the world.",
"Cats can drink seawater.",
"Cats are extremely sensitive to vibrations. Cats are said to detect earthquake tremors 10 or 15 minutes before humans can.",
"A cat's heart beats nearly twice as fast as a human heart, at 110 to 140 beats a minute."
]

def can_play(session_attr):
    return session_attr['facts_index'] < len(cat_facts)

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        attr = handler_input.attributes_manager.persistent_attributes
        if not attr:
            attr['times_played'] = 0
            attr.setdefault("facts_index", -1)
        handler_input.attributes_manager.session_attributes = attr
        if can_play(attr):
            speech_text = f"Welcome to {SKILL_NAME}. Want to play?"
            reprompt = "Say yes to play the game or no to quit."
        else:
            speech_text = f"""
                            Welcome to {SKILL_NAME}. 
                            There are no more cat facts for me to tell you. 
                            Start a new game to rehear the facts or say no to quit.
                           """
            reprompt = "Say start a new game to hear cat facts or no to quit."
        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response


class FactNumberIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("FactNumberIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        fact_number = int(slots["fact_number"].value)
        if 1 <= fact_number <= 10:
            fact_index = fact_number - 1
            session_attr = handler_input.attributes_manager.session_attributes
            session_attr["facts_index"] = fact_index
            speech_text = f"""
                            Here's cat fact number {fact_number}: {cat_facts[fact_index]} 
                            Want to hear another fact?
                           """
            reprompt = "Say yes to hear a cat fact or no to quit."

        else:
            speech_text = """
                           I only know ten facts. 
                           Try saying a number between 1 and 10 to get a fact.
                          """
            reprompt = "Say a number between 1 and 10 to get a fact."

        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response

class StartOverIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.StartOverIntent")(handler_input)

    def handle(self, handler_input):
        # restart playing the facts from the first one
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["facts_index"] = -1
        speech_text = f"You'll now start a new {SKILL_NAME} game. Want to hear a new fact?"
        reprompt = "Say yes to hear a new fact or no to stop the game."
        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speech_text = "I will tell you a fun fact about cats."
        reprompt = "Say yes to hear a fact."

        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response

def persist_user_attributes(handler_input):
    session_attr = handler_input.attributes_manager.session_attributes
    session_attr['times_played'] += 1

    handler_input.attributes_manager.persistent_attributes = session_attr
    handler_input.attributes_manager.save_persistent_attributes()

class StopOrCancelIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.StopIntent")(handler_input) or \
            is_intent_name("AMAZON.CancelIntent")(handler_input)

    def handle(self, handler_input):
        speech_text = f"Thank you for playing {SKILL_NAME}!"
        persist_user_attributes(handler_input)
        handler_input.response_builder.speak(
            speech_text).set_should_end_session(True)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        print(
            f"Reason for ending session: {handler_input.request_envelope.request.reason}")
        persist_user_attributes(handler_input)
        return handler_input.response_builder.response

class YesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.YesIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr.setdefault("facts_index", -1)
        session_attr["facts_index"] += 1
        if can_play(session_attr):
            current_fact = cat_facts[session_attr["facts_index"]]
            speech_text = f"Here's a cat fact: {current_fact} Want to hear another fact?"
            reprompt = "Say yes to hear a cat fact or no to quit."
        else:
            speech_text = """
                           There are no more cat facts for me to tell you. 
                           Start a new game to rehear the facts or say no to quit.
                          """
            reprompt = "Say start a new game to hear cat facts or no to quit."

        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response

class NoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.NoIntent")(handler_input)

    def handle(self, handler_input):
        speech_text = "See you soon!"
        persist_user_attributes(handler_input)
        handler_input.response_builder.speak(
            speech_text).set_should_end_session(True)
        return handler_input.response_builder.response

class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        speech_text = f"""
                        I cannot help you with that.
                        I'm the {SKILL_NAME} and I will share cat facts with you.
                        Want to hear a new fact?
                       """
        reprompt = "Say yes to start the game or no to quit."

        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response

class AllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        print(f"Encountered following exception: {exception}")
        speech = "I don't understand that. Please say it again. "
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response

def get_device_id(handler_input):
    return ask_sdk_dynamodb.partition_keygen.device_id_partition_keygen(
        handler_input.request_envelope
    )

def get_user_id(handler_input):
    return ask_sdk_dynamodb.partition_keygen.user_id_partition_keygen(
        handler_input.request_envelope
    )

class LoggingRequestInterceptor(AbstractRequestInterceptor):
    def process(self, handler_input):
        print(f"Incoming request {handler_input.request_envelope}")
        print(f"user id {get_user_id(handler_input)}")
        print(f"device id {get_device_id(handler_input)}")

class LoggingResponseInterceptor(AbstractResponseInterceptor):
    def process(self, handler_input, response):
        print(f"Response : {response}")


sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(FactNumberIntentHandler())
sb.add_request_handler(StartOverIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(StopOrCancelIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(NoIntentHandler())
sb.add_request_handler(FallbackIntentHandler())



sb.add_exception_handler(AllExceptionHandler())

sb.add_global_request_interceptor(LoggingRequestInterceptor())

sb.add_global_response_interceptor(LoggingResponseInterceptor())

handler = sb.lambda_handler()