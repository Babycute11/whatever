import html

__mod_name__ = "Markdown"

__help__ = f"""
Markdown is a very powerful formatting tool supported by telegram. @RajniiRobot has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.
• _italic_: wrapping text with '_' will produce italic text
• *bold*: wrapping text with '*' will produce bold text
• `code`: wrapping text with '`' will produce monospaced text, also known as 'code'
• [sometext](www.url.com): this will create a link - the message will just show ‘sometext’, \
and tapping on it will open the page at ‘www.url.com’.
<b>Example:</b>
`[test](example.com)`
• `[buttontext](buttonurl:url.com)`: this is a special enhancement to allow users to have telegram \
buttons in their markdown.
`buttontext` will be what is displayed on the button, and <code>someurl</code> \
will be the url which is opened.
*Example:*
`[This is a button](buttonurl:example.com)`
If you want multiple buttons on the same line, use :same, as such:
[one](buttonurl://example.com)
[two](buttonurl://google.com:same)
This will create two buttons on a single line, instead of one button per line.
Keep in mind that your message *MUST* contain some text other than just a button!
"""
