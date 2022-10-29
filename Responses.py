from datetime import datetime
import pandas as pd
import numpy as np
from telegram.ext import ConversationHandler

pd.options.mode.chained_assignment = None
df = pd.read_csv('dictionary.csv')
test_n = 0
test_wr = 0
test_correct = 0
test_incorrect = 0
sample = list([])
bad = set([])
vocab = set(df.en)
change_index = 0
change_choice = ''

word_to_add = {'en': [], 'ru': [], 'def': [],
               'example': [], 'tag': [],
               'now': [datetime.now()], 'last_check': [datetime.now()],
               'days_before': [0], 'correct': [0],
               'incorrect': [0], 'wr': [0],
               'coefficient': [1]}

test_i = -1
target = ''
native = ''
definition = ''
ex = ''


def sample_generator(input_list):
    global bad
    while len(bad) > 0:
        for i in input_list:
            if i in bad:
                yield i
    yield -1


sample_gen = sample_generator(sample)

C = 0.1


def set_c(data):
    data['wr'] = data.correct / (data.correct + data.incorrect)
    data['now'] = datetime.now()
    data['days_before'] = (data.now - pd.to_datetime(data.last_check)).apply(lambda x: x.days)
    data['wr'] = data['wr'].apply(lambda x: 0 if pd.isna(x) else x)
    data['coefficient'] = np.exp(C * (1 - (np.log(data['days_before'] + 1) + 1) / data['wr']))
    data = data.sort_values('coefficient', ascending=True)
    return data


def update_df():
    global df
    df = pd.read_csv('dictionary.csv')
    df = set_c(df)
    df.to_csv('dictionary.csv', index=False)


update_df()


def start_command(updates, _):
    update_df()
    updates.message.reply_text('This bot is based on flash cards.\n If you want some help, just type /help below.')


def help_command(updates, _):
    updates.message.reply_text('If you wanna start, just put your new word, then put its translation, definition on '
                               'target language, example of usage and its tag. \n'
                               'If you want to test your words, just write /test.\n'
                               '/view command will show your own dictionary. \n'
                               '/search some_word and /delete some_word do certain job with word,'
                               ' you have typed after space\n'
                               '/test number tag command starts test with selected number '
                               'and tag of words. This test based on space learning technique.')


def time_command(updates, _):
    updates.message.reply_text(f'Right now {datetime.now()}')


def handle_message(update, _):
    word_to_add['en'] = [update.message.text.lower()]
    update.message.reply_text(f'Your word is {update.message.text.lower()}.\nEnter its translation: ')
    return 1


def translation_message(update, _):
    word_to_add['ru'] = [update.message.text.lower()]
    update.message.reply_text(f'Your translation is {update.message.text.lower()}.\nEnter its definition:')
    return 2


def definition_message(update, _):
    word_to_add['def'] = [update.message.text.lower()]
    update.message.reply_text(f'Your definition is "{update.message.text.lower()}".\nEnter example or put /skip:')
    return 3


def example_message(update, _):
    word_to_add['example'] = [update.message.text.lower()]
    update.message.reply_text(f'Your example is "{update.message.text.lower()}".\nEnter its tag:')
    return 4


def skip_example_command(update, _):
    word_to_add['example'] = ['']
    update.message.reply_text(f'You have skipped example. \nEnter its tag:')
    return 4


def tag_message(update, _):
    global df
    df = pd.read_csv('dictionary.csv')
    word_to_add['tag'] = [update.message.text.lower()]
    df = df.append(pd.DataFrame.from_dict(word_to_add))
    df = set_c(df)
    df.to_csv('dictionary.csv', index=False)
    update.message.reply_text(f'Your tag is {update.message.text.lower()}.\n'
                              f'Word {word_to_add["en"][0]} is successfully added.')
    return ConversationHandler.END


def cancel_command(update, _):
    update.message.reply_text("This word won't be added")
    return ConversationHandler.END


def search_command(update, context):
    update_df()
    word = " ".join(context.args)
    this_word = df[df['en'] == word]
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
    global df, change_index
    update_df()
    word = " ".join(context.args)
    this_word = df[df['en'] == word]
    if len(this_word.index) == 0:
        update.message.reply_text("This word doesn't exist.")
        return ConversationHandler.END
    change_index = this_word.index[0]
    update.message.reply_text(f'The word you want to change:\n'
                              f'Its translation: {this_word["ru"][change_index]}, '
                              f'its meaning: {this_word["def"][change_index]}, '
                              f'example of using this word: {this_word["example"][change_index]}, '
                              f'its tag: {this_word["tag"][change_index]}.')
    update.message.reply_text(f'Select what you want to change and click on /trans, /def, /example or /tag.')
    return 1


def change(update, _):
    global df
    df[change_choice][change_index] = update.message.text.lower()
    df.to_csv('dictionary.csv', index=False)
    update.message.reply_text('You changed word successfully.')
    return ConversationHandler.END


def change_trans(update, _):
    global change_choice
    change_choice = 'ru'
    update.message.reply_text('Write new translation')
    return 2


def change_def(update, _):
    global change_choice
    change_choice = 'def'
    update.message.reply_text('Write new definition')
    return 2


def change_example(update, _):
    global change_choice
    change_choice = 'example'
    update.message.reply_text('Write new example')
    return 2


def change_tag(update, _):
    global change_choice
    change_choice = 'tag'
    update.message.reply_text('Write new tag')
    return 2


def delete_command(update, context):
    global df
    update_df()
    word = " ".join(context.args)
    this_word = df[df['en'] == word]
    if len(this_word.index) == 0:
        update.message.reply_text("This word doesn't exist")
        return 0
    index = this_word.index[0]
    word_str = this_word['en'][index]
    df = df.drop(index, axis=0)
    df.to_csv('dictionary.csv', index=False)
    update.message.reply_text(f'Word {word_str} was deleted successfully')
    return 0


def view_command(update, context):
    global df
    update_df()
    if len(context.args) == 0:
        update.message.reply_text(str(df))
        return 0
    view_tag = str(context.args[0])
    update.message.reply_text(str(df[df['tag'] == view_tag]))
    return 0


def get_next_word(gen, update):
    global test_i, target, native, definition, ex, df
    test_i = next(gen)
    if test_i > -1:
        target = df['en'][test_i]
        native = df['ru'][test_i]
        definition = df['def'][test_i]
        ex = df['example'][test_i]
        df['last_check'][test_i] = datetime.now()
        update.message.reply_text(f'Ru: {native}\nDefinition: {definition}')


def test_command(update, context):
    global test_wr, test_correct, test_incorrect, sample, sample_gen, bad, df, test_i, test_n
    test_n = int(context.args[0])
    update_df()
    test_wr = 0
    test_correct = 0
    test_incorrect = 0
    test_tag = " ".join(context.args[1:])
    if test_tag == '':
        sample = list((df.iloc[:test_n, :]).index)
    else:
        sample = list((df[df.tag == test_tag].iloc[:test_n, :]).index)

    if len(sample) == 0:
        update.message.reply_text(f"Tag {test_tag} doesn't exist")
        return ConversationHandler.END
    sample_gen = sample_generator(sample)
    bad = set(sample)

    update.message.reply_text(f'Test with {test_n} words is beginning.')
    get_next_word(sample_gen, update)
    return 1


def stop_test(update, _):
    update.message.reply_text(f'You just stopped test.\nYour score was {test_wr}.')
    df.to_csv('dictionary.csv', index=False)
    return ConversationHandler.END


def check_word(update, _):
    global bad, sample, sample_gen, df, test_correct, test_incorrect, test_wr

    my_word = str(update.message.text).lower()
    if my_word == target:
        update.message.reply_text(f'Correct! Example: {ex}')
        test_correct = test_correct + 1
        test_wr = test_correct / (test_correct + test_incorrect)
        df['correct'][test_i] += 1
        bad.remove(test_i)
    else:
        update.message.reply_text(f'Incorrect!\nCorrect one is {target}.')
        test_incorrect = test_incorrect + 1
        test_wr = test_correct / (test_correct + test_incorrect)
        df['incorrect'][test_i] += 1

    get_next_word(sample_gen, update)

    if test_i == -1:
        update.message.reply_text(f'You have just completed test successfully.\nYour final score is {test_wr}')
        df.to_csv('dictionary.csv', index=False)
        return ConversationHandler.END
    return 1


def error(update, context):
    update.message.reply_text(f'Update {update} caused error {context.error}')
