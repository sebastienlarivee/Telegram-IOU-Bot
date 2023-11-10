import re
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import database as db
import os

# Connect to the database and create tables if they don't exist
conn = db.connect_db()
db.create_tables(conn)


def parse_message(text: str):

  # Check if the message fits the "{name1} owes {name2} {amount} for {reason}" format
  text = text.lower().strip()
  match = re.match(
    r"(.+) (owes?|owe) (.+) ((?:\d+(\.\d+)?(?:/|-|\+|\*)\d+(\.\d+)?|\d+(\.\d+)?))(?: for)? ?(.*)?",
    text)
  if match:
    debtor, _, creditor, amount, *reason = match.groups()
    reason = ' '.join(part for part in reason if part is not None).strip()

    # Evaluate the amount if it's a formula
    if any(op in amount for op in ('/', '-', '+', '*')):
      amount = str(eval(amount))

    return debtor, creditor, float(amount), reason
  return None


def calculate_totals(group_id: str):
  conn = db.connect_db()
  transactions = db.get_transactions(conn, group_id)

  # Calculate how much each person owes each other person
  totals = {}
  for debtor, creditor, amount in transactions:
    if debtor not in totals:
      totals[debtor] = {}
    if creditor not in totals[debtor]:
      totals[debtor][creditor] = 0
    totals[debtor][creditor] += amount

  # Subtract amounts in the opposite direction
  for debtor, creditors in totals.items():
    for creditor, amount in creditors.items():
      if creditor in totals and debtor in totals[creditor]:
        if totals[debtor][creditor] > totals[creditor][debtor]:
          totals[debtor][creditor] -= totals[creditor][debtor]
          totals[creditor][debtor] = 0
        else:
          totals[creditor][debtor] -= totals[debtor][creditor]
          totals[debtor][creditor] = 0

  return totals


def format_totals(totals):
  messages = []
  for debtor, creditors in totals.items():
    for creditor, amount in creditors.items():
      if amount > 0:
        messages.append(
          f"{debtor.title()} owes {creditor.title()} ${amount:.2f}")
  return '\n'.join(messages)


def start(update: Update, context: CallbackContext):
  """Send a message when the command /start is issued."""
  update.message.reply_text(
    'Hello! Send me a message in the format "{name1} owes {name2} {amount} for {reason}" to track IOUs.'
  )


def totals(update: Update, context: CallbackContext):
  """Send a message with the totals when the command /totals is issued."""
  group_id = str(update.effective_chat.id)
  totals = calculate_totals(group_id)
  message = format_totals(totals)
  if not message:
    message = "No transactions yet!"
  update.message.reply_text(message)


def handle_message(update: Update, context: CallbackContext):
  """Handle incoming messages."""
  group_id = str(update.effective_chat.id)
  text = update.message.text
  transaction = parse_message(text)
  if transaction:
    debtor, creditor, amount, reason = transaction
    conn = db.connect_db()
    db.add_transaction(conn, group_id, debtor, creditor, amount, reason)
    if reason:
      update.message.reply_text(
        f"Added transaction: {debtor.title()} owes {creditor.title()} ${amount:.2f} for {reason}"
      )
    else:
      update.message.reply_text(
        f"Added transaction: {debtor.title()} owes {creditor.title()} ${amount:.2f}"
      )


def history(update: Update, context: CallbackContext):
  """Send a message with the transaction history when the command /history is issued."""
  group_id = str(update.effective_chat.id)
  conn = db.connect_db()
  transactions = db.get_history(conn, group_id)
  if transactions:
    messages = []
    for debtor, creditor, amount, reason, date in transactions:
      if reason:
        messages.append(
          f"{debtor.title()} owes {creditor.title()} ${amount:.2f} for {reason} on {date}"
        )
      else:
        messages.append(
          f"{debtor.title()} owes {creditor.title()} ${amount:.2f} on {date}")
    message = "\n".join(messages)
  else:
    message = "No transactions yet!"
  update.message.reply_text(message)


def main():
  """Start the bot."""
  # Replace 'TOKEN' with your Bot's API token.
  updater = Updater(os.environ['TOKEN'])

  dispatcher = updater.dispatcher

  dispatcher.add_handler(CommandHandler("start", start))
  dispatcher.add_handler(CommandHandler("totals", totals))
  dispatcher.add_handler(CommandHandler("history", history))
  dispatcher.add_handler(
    MessageHandler(Filters.text & ~Filters.command, handle_message))

  # Start the Bot
  updater.start_polling()
  updater.idle()


if __name__ == '__main__':
  main()
