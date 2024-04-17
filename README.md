# Akula Bot

Akula Bot is a powerful and versatile Discord bot designed to enhance your server's functionality and user experience. With its advanced features and seamless integration with the Twitch API, Akula Bot allows you to stay up-to-date with your favorite streamers and receive real-time notifications when they go live.

## Features

- **Streamer Notifications**: Get notified when your favorite streamers start streaming on Twitch.
- **Customizable Notification Modes**: Choose between opt-in, global, and passive notification modes to tailor the bot's behavior to your server's preferences.
- **Easy Configuration**: Server owners can easily configure the bot's settings using intuitive commands and a user-friendly interface.
- **Secure and Reliable**: Akula Bot is built with security and reliability in mind, ensuring a stable and trustworthy experience for your server.

## Adding Akula Bot to Your Server

To add Akula Bot to your Discord server, follow these simple steps:

1. Click on the following invite link: [Invite Akula Bot](https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_CLIENT_ID&permissions=YOUR_BOT_PERMISSIONS&scope=bot)
2. Select the server you want to add the bot to from the dropdown menu.
3. Grant the necessary permissions for the bot to function properly.
4. Click "Authorize" to complete the process.

Once the bot is added to your server, it will automatically create a default configuration and send a welcome message with further instructions.

## Configuration

Akula Bot offers a range of configuration options to customize its behavior and adapt to your server's needs. Server owners can use the following commands to configure the bot:

- `!changeconfig`: Opens the configuration menu, allowing you to modify the bot's settings, such as the notification channel and notification mode.

The bot supports three notification modes:

1. **Opt-In**: Users must manually opt-in to receive notifications for specific streamers using the `!notify` command. Notifications will mention users individually.
2. **Global**: The bot will mention `@everyone` or `@here` (if it has the necessary permissions) when posting notifications in the designated notification channel.
3. **Passive**: The bot will post notifications in the designated notification channel without mentioning anyone.

Note: In the opt-in mode, users can use the `!notify` and `!unnotify` commands to manage their streamer subscriptions. In the global and passive modes, only the server owner can use these commands.

## Commands

Akula Bot provides the following commands for users and server owners:

- `!notify <streamer1> [<streamer2> ...]`: Subscribes the user to notifications for the specified streamers. Streamers can be provided as Twitch usernames, IDs, or URLs.
- `!unnotify <streamer1> [<streamer2> ...]`: Unsubscribes the user from notifications for the specified streamers. Streamers can be provided as Twitch usernames, IDs, or URLs.
- `!notifs`: Displays the list of streamers the user is currently subscribed to for the server that the command was executed in.
- `!changeconfig`: (Server Owner Only) Opens the configuration menu to modify the bot's settings for the server (notification channel and mode).

Note: The `!notify` and `!unnotify` commands can be used by all users in the opt-in mode, but only by the server owner in the global and passive modes.

## Support and Feedback

If you encounter any issues, have questions, or would like to provide feedback, please join our [Support Server](https://discord.gg/YOUR_SUPPORT_SERVER) or open an issue on our [GitHub repository](https://github.com/YOUR_USERNAME/akula-bot).

We value your feedback and are constantly working to improve Akula Bot to provide the best experience for our users.

## Contributing

We welcome contributions from the community to help improve and expand the capabilities of Akula Bot. If you would like to contribute, please read our [Contributing Guidelines](CONTRIBUTING.md) and submit a pull request on our [GitHub repository](https://github.com/Esk3tit/akula-bot).

---

Thank you for choosing Akula Bot! We hope it brings value and enhances the experience for your Discord server and its members.