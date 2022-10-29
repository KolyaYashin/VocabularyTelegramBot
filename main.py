import Constants as Keys
from telegram.ext import *
import Responses as Resp
import pandas as pd
from multiprocessing import Process

pd.options.mode.chained_assignment = None

pid = "/tmp/bot.pid"


def main():
    updater = Updater(Keys.API_KEY, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', Resp.start_command))
    dp.add_handler(CommandHandler('help', Resp.help_command))
    dp.add_handler(CommandHandler('search', Resp.search_command))
    dp.add_handler(CommandHandler('view', Resp.view_command))
    dp.add_handler(CommandHandler('delete', Resp.delete_command))
    dp.add_handler(CommandHandler('time', Resp.time_command))
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('change', Resp.change_start)],
        states={
            1: [CommandHandler('trans', Resp.change_trans), CommandHandler('def', Resp.change_def),
                CommandHandler('example', Resp.change_example), CommandHandler('tag', Resp.change_tag)],
            2: [MessageHandler(Filters.text, Resp.change)]
        },
        fallbacks=[CommandHandler('cancel', Resp.cancel_command)]
    ))
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('test', Resp.test_command)],
        states={
            1: [CommandHandler('stop', Resp.stop_test), MessageHandler(Filters.text, Resp.check_word)]
        },
        fallbacks=[CommandHandler('cancel', Resp.cancel_command)]
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[MessageHandler(Filters.text, Resp.handle_message)],
        states={
            1: [MessageHandler(Filters.text, Resp.translation_message)],
            2: [MessageHandler(Filters.text, Resp.definition_message)],
            3: [CommandHandler('skip', Resp.skip_example_command), MessageHandler(Filters.text, Resp.example_message)],
            4: [MessageHandler(Filters.text, Resp.tag_message)]
        },
        fallbacks=[CommandHandler('cancel', Resp.cancel_command)]
    ))

    dp.add_error_handler(Resp.error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    process = Process(target=main, daemon=True)
    process.start()
    process.join()
