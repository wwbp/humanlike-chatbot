from asgiref.sync import sync_to_async

async def save_chat_to_db(conversation_id, speaker_id,bot_name, text):
    try:
        await sync_to_async(Chat.objects.create)(
            conversation_id=conversation_id,
            speaker_id=speaker_id,
            bot_name=bot_name,
            text=text
        )
        print(f"Successfully saved {speaker_id}'s message to the database.")
    except Exception as e:
        print(f"Failed to save message to the database: {e}")
