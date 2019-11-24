It's my pleasure to gift the community RaceEssentials, an all-encompassing app I've been working on lately. I've tailored it to bring together a large number of relevant data and to display it logically and clearly. The app monitors over 30 useful parameters crucial for almost every type of driving session. AB track types as well as classic circuit tracks are fully supported. I also have to thank Jorge Alves, who wasn't directly involved in the app development, but his StatsBar Plus app inspired me to make this one and I had a look or two in his code to figure out some logic.

Download the app at RaceDepartment:
http://www.racedepartment.com/downloads/raceessentials.10016/

A quick overview of how the app works and what it's capable of:

1. Gear, goes red when near limiter.
2. Speed, can be set to either kph or mph.
3. Rpm, graphical and numerical, goes red when near limiter.
4. Turbo boost, graphical and numerical.
5. KERS, graphical and numerical. The bar is green when stored energy is currently in use, otherwise it's blue.
6. ABS, Traction Control and DRS indicators.
7. Current lap time, goes red when lap is invalid.
8. Current ambient and track temperatures.
9. Last lap time, goes red when last lap was invalid.
10. Best lap time, only displayed if best lap was valid.
11. Personal best lap time, only valid laps are saved (per track/car combo).
12. Tyre info area; the bar on the right represents tyre wear scaled from 94% to 100% and colored accordingly from red to green, similar to official Kunos app (below 94% the bar remains its minimum size). Tyre slip is also shown here, the bars go darker when slip ratio increases. Tyre wear values (can be toggled), core temperature values (currently only in Celsius) and pressures (currently only in psi) are displayed on the left of each tyre and colored accordingly.
13. Delta best and delta personal best using normalized spline position and interpolation (original idea and implementation by Erwin Schmidt). Various checks are implemented to avoid erratic behavior and to maximize accuracy. Click or press Alt + D to switch between best and personal best delta.
14. Delta bar (shows whether you're losing or gaining time at the particular moment). 
15. Current position in the ongoing event.
16. Current lap number and total laps number.
17. Clutch, brake and gas pedal bars, together with FFB clipping bar, basically a pedals app clone.
18. Remaining time in a session, goes red when under 5 minutes, plus a real life clock.
19. Fuel information area with current fuel level, consumption per lap, how many laps are left in the tank and how much fuel is required to complete the race (red if insufficient). Consumption per lap works after the first completed lap and keeps track of all previous laps, not only the last one. If the driver topped up during the lap, that lap will be ignored.
20. Current track grip.
21. Tyre compound short name along with optimal compound temperatures or pressures (click or press Alt + C to toggle).

A quick FAQ (please read before posting in the support thread):

Q: How do I install this app?
A: Unpack the contents of the zip file in your AC install directory and enable it in Settings. Then, once on the track, turn it on from the vertical apps menu on the right.

Q: I've enabled the app in Settings and turned it on in the apps menu but it's not working.
A: Try one of the following:
- Disable all apps in Settings except RaceEssentials and see if it works (if that works, start re-enabling apps one by one to see which one was at fault)
- From Documents/Assetto Corsa/cfg folder delete python.ini file, and enable only RaceEssentials in settings (again, if that works, start re-enabling apps one by one to see which one was at fault)
- If none of the above worked: delete python.ini file (yes, again), delete the entire apps folder (backup it first just in case) from your AC install directory (often found in C:\Program Files (x86)\Steam\steamapps\common\assettocorsa) and run Steam integrity check. After that, reinstall RaceEssentials only and try if it works. If all is ok, only then start adding back one by one the apps you previously had.
- Ultimately if it's still broken, open console while in game by pressing Home key on your keyboard and paste any errors in the support thread.

Q: What can I customize?
A: If you open config.ini in apps/python/RaceEssentials you'll find several customizable parameters including scaling, mph/kph toggle, opacity, centralized gear option...

Q: ABS and TC are not realtime?
A: They indicate if the respective systems are on or off, no way to tell if they're in use at the precise moment, Kunos pls? :)

Q: How do the new optimal shift point rpm lights work?
A: The app pulls data from the file used to draw the power/torque graph in the launcher and uses it to automatically figure out the optimal shift point for each car. On many cars, you won't notice any difference since the engines' maximum power output is very high in the rpm range. But, some cars like SF15-T, Ferrari 458 GT2 and Ferrari 488 GT3 (and many more) reach maximum power on rpms way before the engine hits the limiter. Before, the only way to know when to shift correctly on these cars was to look at their dash or steering wheel rpm lights, which can be very inconvenient due to camera choice, FOV, PP filter, steering wheel visibility settings and so on... Now, the app will automatiacally detect optimal shift points and trigger the rpm lights optimally and automatically, per car, without the need to adjust anything. Also, the app detects if the optimal shift point is beyond the limiter and reverts to old behaviour in that case. If for some crazy reason you don't want any of this awesomeness, you can turn it off in the config.ini, and also adjust the trigger tolerances (although I don't recommend this either).

Q: Mod cars don't have colored temperature and pressure values?
A: I have no way of knowing the ideal temperature and pressure values for non-Kunos cars. You can, however, add this info yourself as long as the mod car provides a tyre short name (S, M, H...) by making an *.ini file in compounds folder. An example (using RSR Formula 3) is provided. The *.ini file must have the same name as the car folder in content/cars and must follow the structure provided in the example.

Q: Delta is not shown?
A: You're either on an outlap, you've visited the pit in the current lap or you haven't done a valid lap yet to compare with.

Q: How do the ERS/KERS bars work?
A: Bar shows the remaining battery charge, it's green when the energy is being consumed and blue when it isn't. Bottom half bar only shows on cars that have limited energy consumption per lap and shows how much more energy you're allowed to use in that lap.

Q: Can I transfer my PB folder to/from Sidekick?
A: Yes!

Version history:

v1.4.3
- Added all Tripl3 Pack car data to ideal temperatures and pressures list (+Audi A1 S1)
- Entering pit lane now invalidates both lap time and relevance for fuel calculations
- Slightly improved outlap detection
- Updated the shared memory Sim Info with the new AC 1.8 parameters

v1.4.2
- Added some more robustness to the code that loads max power data since Kunos for some reason used 3 different character encodings, seemingly randomly

v1.4.1
- Fixed a bug where the rpm bar was not visible

v1.4
- Awesome new rpm lights! They now automatically show optimal shift points per car, check FAQ for more info
- Updated the shared memory Sim Info with the new AC 1.7.2 parameters

v1.3
- Added DRS indicator with DRS zone detection
- Overhauled the code behind ERS/KERS monitoring, now with a bar showing how much energy is allowed to be spent in a lap (currently only used for F138 and SF15-T)
- Updated the shared memory Sim Info with the new AC 1.7.1 parameters

v.1.2.3
- Added all Red Pack car data to ideal temperatures and pressures list (+Maserati Levante)
- Ideal pressures and temperatures for mod cars are now easier to add and won't be overwritten by updates (check FAQ for details)

v1.2.2
- TC/ABS/DRS states are now cached to avoid unnecessary draw calls (thanks to Yachanay)
- Lap start now clears lap validity as well (no need to complete invalid laps on Nord Tourist any more), configurable from config.ini
- Fixed a bug where invalid lap could be saved as best/personal best if slower valid lap time is set after it
- Keyboard shortcuts remapped to Alt + D (delta button) and Alt + C (compound button)

v1.2.1
- A small fix for a problem that prevented the app from initializing under certain circumstances
- A tiny fix for generating config.ini

v1.2
- A lovely new delta bar, shows how quickly you're improving/degrading your lap time in that particular moment (thanks @Lord Kunos for the idea)
- Configurable stuff is now saved in separate file for easier customization (from now on, edit only config.ini in apps/python/RaceEssentials; personal settings will not be overwritten by updates any more)
- Added the option to swap tyre section with gear/speed section, off by default, customize it in config.ini
- Implemented HotKeys for delta (F4) and compound (F7) so you can bind them to your wheel and not chase around the screen with mouse in the middle of the race
- Added how short you are on fuel to finish the race; if you don't have enough fuel to finish, the label will cycle between required fuel and how much you need to fill up
- Track grip and ambient/road labels have switched positions, probably more logical to have track grip next to compound info
- Track grip value is now displayed with one decimal place

v1.1.1
- Fixed the bug where lap times slower than best/personal best were incorrectly displayed after best/personal best was beaten in the current session
- A tiny fix for fuel consumption calculation
- Fancy new app icon for the sidebar
- Couple of small shuffles in the code

v1.1
- Fixed the stuff that got broken with AC 1.6 update
- Added all Japanese DLC car data to ideal pressures and temperatures list
- Tyre wear numerical value is now shown by default (and scaled from 94% to 100%); Scale value can be customized and numerical tyre wear can be disabled completely (für zee immersion reasons)
- Tyre slip ratio implemented, the tyre wear bars now go darker when tyre slip ratio increases
- Tyre compound label can now be clicked and toggles between ideal pressures (front/rear) and ideal temperatures (from-to)
- Some layout changes to better accommodate new data (pedals and fuel got a bit skinnier, tyre bars grew a bit and some label positions got shuffled)
- Updated the shared memory Sim Info with the new AC 1.6 parameters
- Disk writes are now only done on AC shutdown to prevent possible micro freezes when accessing the disk (especially classic HDDs)
- Fixed the bug where non-Kunos cars had pressures always colored red

v1.0
- A huge update to tyres section, now with coloring according to ideal pressures and temperatures for every Kunos car/tyre combo (check the FAQ for more info)
- Optimal tyre compound temperatures are now displayed next to compound short name
- Implemented delta pacing indicator
- Track grip is now displayed
- Ambient and track temperatures are now displayed
- Added background to all bars for better visibility
- RPM bar is now colored as well when near limiter for better visibility
- Some layout changes to accomodate new data
- A bit of code cleanup here and there

v0.9.2
- A tiny fix for app visibility when loading the game after the replay was previously loaded

v0.9.1
- Fixed the bug where app couldn't be disabled after v0.9 update

v0.9
- Implemented app scaling (check the FAQ to see how to set it up)
- Disabled the app during replays
- Tiny color adjustments
- A bit of optimization here and there

v0.8.4
- A possible fix for people who only had gear indicator displayed
- Added a small delay for updating lap times when crossing the finish line to make sure the correct info has arrived before updating
- Various delta tweaks to ensure no nonsense values are stored or displayed
- Lap number doesn't increment on race finish
- Total number of cars on track is now displayed corretcly when online
- A tiny fix for fuel consuption to make it even more accurate
- Updated the shared memory Sim Info with the new AC 1.5 parameters

v0.8.3
- A workaround for the AC maxRpm shared memory bug
- Tiny change for delta display when crossing the finish line

v0.8.2
- Ensuring the Sim Info instance is private to avoid conflicts with other apps

v0.8.1
- Small change for delta display when crossing the finish line

v0.8
- Initial release