# esp32_catch_the_stars

During a tech maker challange at work people were asked to write a game on an ESP32 board connected to a tiny 0.96 inch OLED monochrome display (SSD1306), a simple button and a buzzer.
So I decided to accept the challange and sat down to right a nice game :-).
The idea is to "catch stars" by hitting them with a ball and making them fall down. You have only 7 balls and you by catching each star you get points. If you hit multiple stars with the same ball you get higher points.

Since I have only one button the user interface is done by two types of clicks: short click (less than 250ms) and long click.

In order to enhance the game's visualization I also added some nice menus and some animations when the level is completed.
