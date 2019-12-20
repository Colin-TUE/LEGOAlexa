# Setting up your Alexa and Turtle

This documents describes how to setup your Alexa and Turtle. This project is based upon the resources provided by Amazon and LEGO in the [LEGO Mindstorms Voice Challenge](https://www.hackster.io/alexagadgets/lego-mindstorms-voice-challenge-setup-17300f). This setup will guide you directly towards a working Turtle.

![Warning](emoticons/warning-sign_26a0_s.png) This guide assumes the reader can find its way around the Developer Console, EV3Dev, and VSCode. If that is not the case we strongly recommend to follow the Setup guide provided by LEGO and Amazon before programming the Turtle.

![Information](emoticons/information-source_2139_s.png) If you continue from the provided Setup (and missions), then most of the prepare sections below are already covered. In that case we advise to start with the "Setup Communication between Alexa and EV3" section.

## Preparing the Development Environment

First download and install [Visual Studio Code](https://code.visualstudio.com/) and then download/clone the [project sources](https://github.com/Colin-TUE/LEGOAlexa). Open the project directory in VSCode and install the recommended set of extensions. You can install when clicking "Install All" in the "recommended extensions popup" or manually by opening the "Extensions" panel.

The required extensions are:

- ev3dev-browser (version 1.0.4)
- Python (version 2019.11.50794)

## Preparing the Mindstorms Brick

To be able to program and connect the Mindstorms brick, you need to install [EV3Dev](https://www.ev3dev.org/). Follow [these instructions](https://www.ev3dev.org/docs/getting-started/) to get EV3Dev running on the Mindstorms brick.

After installing EV3Dev, boot EV3Dev on the Mindstorms brick. Make sure the brick has a connection to your computer, either via WiFi or using the provided USB cable. When connecting using WiFi, the brick should show it's IP address in the upper left corner.

## Preparing Alexa

SO now the EV3 is setup and ready to be controlled. In this section we will setup Alexa to be ready to control the EV3. First you need to create an Alexa Gadget. Sign in to [https://developer.amazon.com](https://developer.amazon.com). Sign up for a developer account if you don't already have one. Then open the "Alexa Voice Service" in the "Developer Console" and create a product. Fill out the requested information:

- Name: MINDSTORMS EV3
- Product ID: EV3_01
- Product type: Alexa Gadget
- Product category: Animatronic or Figure
- Product description: Whatever you like
- Skip upload image
- Do you intend to distribute this product commercially?: No
- Is this a children’s product or is it otherwise directed to children younger than 13 years old?: No

Now you will see an overview of your products. Click on the just created product (probably named "Mindstorms EV3").

## Setup Communication between Alexa and EV3

In the `ev3-code-python/` folder, copy the `soccerTurtle.example.ini` file and rename the copy to `soccerTurtle.ini`. Then copy the "Amazon ID" and "Alexa Gadget Secret" to their respective fields inside the `soccerTurtle.ini`. This configures your EV3 and Alexa to know who they are talking to.

![Information](emoticons/information-source_2139_s.png) It is advised to open the `ev3-code-python` folder in a separate VSCode window, so that VSCode only has to synchronize the EV3 code and not the READMEs, attachments, or the Skill code.

In the EV3Dev Browser in VSCode, click to connect to the EV3. Once you are connected a green dot should appear next to the brick's name. Click on "Send workspace to device" to upload the python code to the EV3.

For the just setup Alexa Gadget, we will create an Alexa Skill that controls the EV3. So in the ["Developer Console"](https://developer.amazon.com/alexa/console/ask) click on "Create Skill". Select a "Custom" model and "Alexa-Hosted (Node.js)" provision resource. (For a Template the "Hello World Skill" is good enough.) Once created, it opens the Skill configuration. Open the "Interfaces" sub-menu and enable the "Custom Interface Controller". Click on "Save Interfaces". For the "Interaction Model" open the "JSON Editor" and copy the contents of the `skill-code-nodejs/model.json`. Click on "Save Model"and then "Build Model". This will load the Turtle interaction model to your Alexa device.

Once the model has been trained, open the "Code" tab and copy the contents of each file in the `skill-code-nodejs/lambda` folder to their respective files in this "Code" tab. (You might need to click on "Create file" before copying the contents of `common.js`.) Once copied, click on "Save" and then "Deploy". This will save the files and deploy them so that Alexa can use them to coach the Turtle.

Now the code is copied to Alexa and the EV3, we can start the connection between the Alexa device and the EV3. First enable Bluetooth on the EV3 and then run the `soccerTurtle.py` on the EV3. In VSCode you should now see the `Debug Console` indicating that the Ev3 is in pairing mode. Once they are paired, indicated on both the EV3 screen and the `Debug Console`, you can start coaching the Turtle.

## Sources

- [By LEGo and Amazon provided setup and missions](https://www.hackster.io/alexagadgets/lego-mindstorms-voice-challenge-setup-17300f)
- [EV3Dev](https://www.ev3dev.org/)
- [Alexa Developer Console](https://developer.amazon.com/alexa/console/)
- [VSCode](https://code.visualstudio.com/)
