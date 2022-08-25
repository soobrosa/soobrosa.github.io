---
layout: post
title: Talk to Wunderlist in Python
categories: post
date: 2015-05-13
---

# Talk to Wunderlist in Python

Today we’ve publicly released the [Wunderlist API](https://github.com/microsoftarchive/api) so you can programmatically talk to Wunderlist. Being a Python hacker I share some example code on how to do this in practice.

This [Github repo](https://github.com/microsoftarchive/wunderlist-python) contains a simple blueprint on talking to the Wunderlist API and two working examples on pulling your Coursera deadlines into Wunderlist as tasks with due dates and aggregating the Foursquare tips your friends left in your current city into a Wunderlist.

All code is tested on [pythonanywhere.com](https://www.pythonanywhere.com/) with a default Flask deployment on a Hacker account.

You maybe can find a working hosted version of the [Coursera](http://soobrosa.pythonanywhere.com/coursera) and the [Foursquare](http://soobrosa.pythonanywhere.com/foursquare) scripts at my PythonAnywhere account, but they could go offline without any further notice.

Thanks to [Torsten](https://github.com/torsten) for pointing in directions and [Franziska](https://github.com/vsmart) for the simple urllib-based approach on how to talk to the WL API.
