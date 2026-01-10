# Snap-A-Steg

Snap-A-Steg gives users the ability to hide encrypted messages inside ordinary images so they can be shared without anyone knowing a message even exists.

It is designed for situations where simply sending an encrypted message is suspicious, such as under censorship, surveillance, or coercion. Even if an image is intercepted, an attacker cannot easily determine that it contains a message, and without both the encryption key and a user-generated password, recovering the contents of the message is computationally infeasible.

This tool is intended for a variety of different users:
- Journalists and their sources
- Activists and organizers
- People living under surveillance
- Anyone who needs to move secrets without drawing attention to themselves or others

## Features

- Embed secret messages into images with password protection for private and secure messaging
- Decode hidden messages with the correct password and key  
- Overwrite existing messages in images  
- Real-time password strength feedback
- Byte counter to alert how large of a message you can send
- Randomly assigned unique encryption keys for enhanced security
- Simple and intuitive GUI

## Join the Community:

We coordinate development, testing, and support on Discord
**Join the [Snap-A-Steg Discord](https://discord.gg/m9rUbBbHKR)**

## Project Structure
- `snap_a_steg.py`: Main application script with GUI and logic
- `encode_decode.py`: Handles encryption and decryption functions
- `ui_helpers.py`: Utility file to handle various UI functions
- `README.md`: Project overview and instructions
- `LICENSE`: License details



## Installation

1. Clone the repository:  
   ```bash
   git clone https://github.com/argeincharge/snap-a-steg.git
   ```
2. Install dependencies (requires Python 3.8+):
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python snap_a_steg.py
   ```

## Usage
- Load an image file in the app
- Open the Encode popup to write and password-protect your secret message
- Save the encoded image and keep the encryption key safe
- Use the Decode popup to retrieve messages from encoded images

## Screenshots

### Main Interface
![Main UI](screenshots/welcome_screen.png)

### Encode Popup
![Encode Popup](screenshots/encode_popup.png)

### Encode Popup Results
![Encode Popup Results](screenshots/encode_popup_encoded.png)

### Decode Popup
![Decode Popup](screenshots/decode_popup.png)

### Decode Popup Results
![Decode Popup Results](screenshots/decode_popup_decoded.png)


### Security Considerations

Please note that Snap-A-Steg only handles encryption and hiding messages within images. How you share the password and encryption key with the recipient is critical for maintaining security. For best practice, share the password and key through separate, secure channels. For example:

- Send the encrypted image via email, and share the password via SMS or phone call.  
- Use an end-to-end encrypted messaging app to share one of the credentials.  
- Avoid sending both password and key over the same unsecured channel.

Failing to do so can compromise the confidentiality of your messages.
  

## License
This project is licensed under the GNU General Public License v3.0 (GPLv3). See the LICENSE file for details.


Feel free to open issues or submit pull requests!

