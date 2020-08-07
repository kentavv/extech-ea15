# extech-ea15
Decode temperature measurements from an Extech EA15 thermocouple datalogging thermometer. There's a good chance that the related thermometers, even with different number of probe inputs, have a similar protocol. Probably only need to change the number of measurements sent in each packet. I'm willing to add support for additional Extech thermometers sent to me to examine.  

The temperature unit selected on the datalogger is read, but to ensure uniformity, especially within downloaded datalogged measurements, all measurements are converted to C. Without doing this, changing the units during the datalogging would cause the downloaded results to have multiple units. (Might be fine, and preferred, and could be used to flag sections of the recorded data at the instrument.)

Manually logged measurements (quick press of Mem button) cannot be downloaded. Reviewing these (quick press of Read button followed by up or down buttons) are likely to stop serial data until normal run restarts (second quick press of Read button.)

Pressing the Hold button is also likely to block serial. In general, a new measurement is only sent over serial if the display updates.

Written August 6, 2020 by Kent A. Vander Velden kent.vandervelden@gmail.com

# References

[http://www.extech.com/products/resources/EA15_UM-en.pdf](http://www.extech.com/products/resources/EA15_UM-en.pdf)

[http://www.extech.com/products/resources/EA10_EA15_DS-en.pdf](http://www.extech.com/products/resources/EA10_EA15_DS-en.pdf)

[Comparison of thermocouple types](https://www.thermocoupleinfo.com/thermocouple-types.htm)
