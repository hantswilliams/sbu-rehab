<!-- To do -->

## SBU Rehab
- Current local working version: `app` folder
    - `app.py` and `video.html` - uses a physical camera in the app folder 
- Almost working using the web camera in the browser: `app2` folder
    - `app2.py` and `video2.html` - uses the web camera in the browser in the app2 folder
- App3 is the one to go off of 
    - This incoroporate JS versions of pose net that allows for the use of the web camera in the browser with very efficient processing, very fast

## Issues 
- Can currently get app.py to run because it is loading a physical camera. Need to update the logic so it uses the web camera from the browser instead. Otherwise it is hard coded, and when deployed, it will not work.
    - the video2.html and app2.py - which tries to use the exercises/ folder is a attempt to begin to re-factor the code to use the web camera instead of a physical camera.
    - Have a almost working versio nof it in the `app2` folder
