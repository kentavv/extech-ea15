# extech-ea15
Decode temperature measurements from an Extech EA15 thermocouple datalogging thermometer

Temperature unit selected on the datalogger are read but to ensure uniformity, especially within downloaded datalogged measurements, all measurements are converted to C.

Manually logged measurements (quick press of Mem button) cannot be downloaded. Reviewing these (quick press of Read button followed by up or down buttons) are likely to stop serial data until normal run restarts (second quick press of Read button.)

Pressing the Hold button is also likely to block serial. In general, a new measurement is only sent over serial if the display updates.

Written August 6, 2020 by Kent A. Vander Velden kent.vandervelden@gmail.com

# References

[http://www.extech.com/products/resources/EA15_UM-en.pdf](http://www.extech.com/products/resources/EA15_UM-en.pdf)

[http://www.extech.com/products/resources/EA10_EA15_DS-en.pdf](http://www.extech.com/products/resources/EA10_EA15_DS-en.pdf)

[Comparison of thermocouple types](https://www.thermocoupleinfo.com/thermocouple-types.htm)
