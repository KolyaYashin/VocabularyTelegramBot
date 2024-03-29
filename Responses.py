from datetime import datetime
import pandas as pd
import numpy as np
from telegram.ext import ConversationHandler

pd.options.mode.chained_assignment = None
C = 0.2


def sample_generator(input_list, bad):
    while len(bad) > 0:
        for i in input_list:
            if i in bad:
                yield i
    yield -1


def set_c(data):
    data['wr'] = data.correct / (data.correct + data.incorrect)
    data['now'] = datetime.now()
    data['days_before'] = (data.now - pd.to_datetime(data.last_check)).apply(lambda x: x.days)
    data['wr'] = data['wr'].apply(lambda x: 0 if pd.isna(x) else x)
    data['coefficient'] = np.exp(C * (1 - (np.log(data['days_before'] + 1) + 1) / data['wr']))
    data = data.sort_values('coefficient', ascending=True)
    return data


def start_command(updates, _):
    updates.message.reply_text('This bot is based on flash cards.\n If you want some help, just type /help below.')


def help_command(updates, _):
    updates.message.reply_text('If you wanna start, just put your new word, then put its translation, definition on '
                               'target language, example of usage and its tag. \n'
                               '/view command will show your own dictionary. \n'
                               '/search _some_word_ and /delete _some_word_ do certain job with word,'
                               ' you have typed after space\n'
                               '/test _number_ _tag_ command starts test with selected number '
                               'and tag of words. This test based on space learning technique.\n'
                               '/change word command will change selected word. You just need to select\n'
                               'feature you want to change and write new.')


def time_command(updates, _):
    updates.message.reply_text(f'Right now {datetime.now()}')


def handle_message(update, context):
    context.user_data['en'] = update.message.text.lower()
    update.message.reply_text(f'Your word is {update.message.text.lower()}.\nEnter its translation: ')
    return 1


def translation_message(update, context):
    context.user_data['ru'] = update.message.text.lower()
    update.message.reply_text(f'Your translation is {update.message.text.lower()}.\nEnter its definition:')
    return 2


def definition_message(update, context):
    context.user_data['def'] = update.message.text.lower()
    update.message.reply_text(f'Your definition is "{update.message.text.lower()}".\nEnter example or put /skip:')
    return 3


def example_message(update, context):
    context.user_data['example'] = update.message.text.lower()
    update.message.reply_text(f'Your example is "{update.message.text.lower()}".\nEnter its tag:')
    return 4


def skip_example_command(update, context):
    context.user_data['example'] = ''
    update.message.reply_text(f'You have skipped example. \nEnter its tag:')
    return 4


def tag_message(update, context):
    user_id = update.message.chat_id
    data = pd.read_csv(f'data/dictionary_{user_id}.csv')
    context.user_data['tag'] = update.message.text.lower()
    d = context.user_data
    word_to_add = {'en': [d["en"]], 'ru': [d["ru"]], 'def': [d["def"]],
                   'example': [d["example"]], 'tag': [d["tag"]],
                   'now': [datetime.now()], 'last_check': [datetime.now()],
                   'days_before': [0], 'correct': [0],
                   'incorrect': [0], 'wr': [0],
                   'coefficient': [1]}
    data = data.append(pd.DataFrame.from_dict(word_to_add))
    data = set_c(data)
    data.to_csv(f'data/dictionary_{user_id}.csv', index=False)
    update.message.reply_text(f'Your tag is {update.message.text.lower()}.\n'
                              f'Word {word_to_add["en"][0]} is successfully added.')
    return ConversationHandler.END


def cancel_command(update, _):
    update.message.reply_text("This word won't be added")
    return ConversationHandler.END


def search_command(update, context):
    user_id = update.message.chat_id
    data = pd.read_csv(f"data/dictionary_{user_id}.csv")
    word = " ".join(context.args)
    this_word = data[data['en'] == word]
    if len(this_word.index) == 0:
        update.message.reply_text("This word doesn't exist")
        return 0
    index = this_word.index[0]
    update.message.reply_text(
        f'Your words translation is: {this_word["ru"][index]}\nIts meaning: {this_word["def"][index]}\n'
        f'Example of using: {this_word["example"][index]}\n'
        f'Its tag: {this_word["tag"][index]}\n'
        f'Last time this word was checked: {this_word["last_check"][index]}\n'
        f'Your win rate at this word: {this_word["wr"][index]}')
    return 0


def change_start(update, context):
    user_id = update.message.chat_id
    data = pd.read_csv(f"data/dictionary_{user_id}.csv")
    word = " ".join(context.args)
    this_word = data[data['en'] == word]
    if len(this_word.index) == 0:
        update.message.reply_text("This word doesn't exist.")
        return ConversationHandler.END
    context.user_data["change_index"] = this_word.index[0]
    update.message.reply_text(f'The word you want to change:\n'
                              f'Its translation: {this_word["ru"][context.user_data["change_index"]]}, '
                              f'its meaning: {this_word["def"][context.user_data["change_index"]]}, '
                              f'example of using this word: {this_word["example"][context.user_data["change_index"]]}, '
                              f'its tag: {this_word["tag"][context.user_data["change_index"]]}.')
    update.message.reply_text(f'Select what you want to change and click on /trans, /def, /example or /tag.')
    return 1


def change(update, context):
    user_id = update.message.chat_id
    data = pd.read_csv(f"data/dictionary_{user_id}.csv")
    data[context.user_data["change_choice"]][context.user_data["change_index"]] = update.message.text.lower()
    data.to_csv(f'data/dictionary_{user_id}.csv', index=False)
    update.message.reply_text('You changed word successfully.')
    return ConversationHandler.END


def change_trans(update, context):
    context.user_data["change_choice"] = "ru"
    update.message.reply_text('Write new translation')
    return 2


def change_def(update, context):
    context.user_data["change_choice"] = "def"
    update.message.reply_text('Write new definition')
    return 2


def change_example(update, context):
    context.user_data["change_choice"] = "example"
    update.message.reply_text('Write new example')
    return 2


def change_tag(update, context):
    context.user_data["change_choice"] = "tag"
    update.message.reply_text('Write new tag')
    return 2


def delete_command(update, context):
    user_id = update.message.chat_id
    data = pd.read_csv(f"data/dictionary_{user_id}.csv")
    word = " ".join(context.args)
    this_word = data[data['en'] == word]
    if len(this_word.index) == 0:
        update.message.reply_text("This word doesn't exist")
        return 0
    index = this_word.index[0]
    word_str = this_word['en'][index]
    data = data.drop(index, axis=0)
    data.to_csv(f'data/dictionary_{user_id}.csv', index=False)
    update.message.reply_text(f'Word {word_str} was deleted successfully')
    return 0


def view_command(update, context):
    user_id = update.message.chat_id
    data = pd.read_csv(f"data/dictionary_{user_id}.csv")
    if len(context.args) == 0:
        update.message.reply_text(str(data))
        return 0
    view_tag = " ".join(context.args)
    update.message.reply_text(str(data[data['tag'] == view_tag]))
    return 0


def get_next_word(gen, update, context, data):
    context.user_data["test_i"] = next(gen)
    if context.user_data["test_i"] > -1:
        target = data['en'][context.user_data["test_i"]]
        context.user_data['target'] = target
        native = data['ru'][context.user_data["test_i"]]
        context.user_data['native'] = native
        definition = data['def'][context.user_data["test_i"]]
        context.user_data['definition'] = definition
        ex = data['example'][context.user_data["test_i"]]
        context.user_data['ex'] = ex
        update.message.reply_text(f'Ru: {native}\nDefinition: {definition}')
    return


def test_command(update, context):
    test_n = int(context.args[0])
    user_id = update.message.chat_id
    data = pd.read_csv(f"data/dictionary_{user_id}.csv")
    data = set_c(data)
    context.user_data["test_wr"] = 0
    context.user_data["test_correct"] = 0
    context.user_data["test_incorrect"] = 0
    test_tag = " ".join(context.args[1:])
    if test_tag == '':
        sample = list((data.iloc[:test_n, :]).index)
    else:
        sample = list((data[data.tag == test_tag].iloc[:test_n, :]).index)

    if len(sample) == 0:
        update.message.reply_text(f"Tag {test_tag} doesn't exist")
        return ConversationHandler.END
    bad = set(sample)
    sample_gen = sample_generator(sample, bad)
    context.user_data["sample"] = sample
    context.user_data["bad"] = bad
    context.user_data["sample_gen"] = sample_gen
    context.user_data["test_n"] = test_n
    update.message.reply_text(f'Test with {test_n} words is beginning.')
    get_next_word(sample_gen, update, context, data)
    return 1


def stop_test(update, context):
    user_id = update.message.chat_id
    update.message.reply_text(f'You just stopped test.\nYour score was {context.user_data["test_wr"]}.')
    data = pd.read_csv(f"data/dictionary_{user_id}.csv")
    for ind in context.user_data['sample']:
        data.loc[ind, 'last_check'] = datetime.now()
    data = set_c(data)
    data.to_csv(f'data/dictionary_{user_id}.csv', index=False)
    return ConversationHandler.END


def check_word(update, context):
    user_id = update.message.chat_id
    my_word = str(update.message.text).lower()
    df = pd.read_csv(f"data/dictionary_{user_id}.csv")
    if my_word == context.user_data['target']:
        update.message.reply_text(f'Correct! Example: {context.user_data["ex"]}')
        context.user_data["test_correct"] = context.user_data["test_correct"] + 1
        context.user_data["test_wr"] = context.user_data["test_correct"] / \
                                       (context.user_data["test_correct"] + context.user_data["test_incorrect"])
        df['correct'][context.user_data["test_i"]] += 1
        bad = context.user_data["bad"]
        bad.remove(context.user_data["test_i"])
        context.user_data['bad'] = bad
        df.to_csv(f'data/dictionary_{user_id}.csv', index=False)
    else:
        update.message.reply_text(f'Incorrect!\nCorrect one is {context.user_data["target"]}.')
        context.user_data["test_incorrect"] = context.user_data["test_incorrect"] + 1
        context.user_data["test_wr"] = context.user_data["test_incorrect"] / \
                                       (context.user_data["test_correct"] + context.user_data["test_incorrect"])
        df['incorrect'][context.user_data["test_i"]] += 1
        df.to_csv(f'data/dictionary_{user_id}.csv', index=False)

    get_next_word(context.user_data["sample_gen"], update, context, df)

    if context.user_data["test_i"] == -1:
        update.message.reply_text(f'You have just completed test successfully.'
                                  f'\nYour final score is {context.user_data["test_wr"]}')
        for ind in context.user_data['sample']:
            df.loc[ind, 'last_check'] = datetime.now()
        df = set_c(df)
        df.to_csv(f'data/dictionary_{user_id}.csv', index=False)
        return ConversationHandler.END
    return 1


def error(update, context):
    update.message.reply_text(f'Update {update} caused error {context.error}')
