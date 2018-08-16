This document will discuss and explain parts of Python (and project details in general) that are important to know in order to recreate other similar scripts as well as understanding the organization of this one.

[Link](https://rdslade.github.io/CAN-232) to CAN-232 homepage

# Before you read

Before you read about the specifics of this program (and others similar to it), you first should be up to date with the syntax and conecpts of Python and specifically the tkinter module. The following are links that may be helpful in learning the basics through some more complex topics.

[learnpython.org](http://learnpython.org/) is a great resource for getting used to Python syntax and semantics. It has an interactive shell where you can practice your own code and check answers to coding problems. This website can give you a strong base in the fundamentals of Python, but in my opinion falls a bit short at more complex topics such as object orientation. 

[realpython.com](https://realpython.com/python3-object-oriented-programming/) has a great page on object orientation in Python. While there are not many chances to practice on your own, this website has many details to help get you started understanding Python class structure.

[pythonprogramming.net](https://pythonprogramming.net/python-3-tkinter-basics-tutorial/) provides a nice intro into tkinter. The video provides an overview of the topic as well as the basics of creating your displays.

[tutorialspoint.com](https://www.tutorialspoint.com/python/python_gui_programming.htm) has a great list of the tkinter widgets with short descriptions of what each one is, what they are used for, and how to implement them.

# CAN-232 Python Programmer Details

## Main function format

As with any other programming languages, the `main` function should try to be kept short. Putting our code in chunks of modules, we can reduce the amount of code in `main` and reuse much of the code. Here is the main function in it's entirety:

```
### Instantiate the root window and start the Application
if __name__ == "__main__":
    root = tk.Tk()
    a1 = Application(root)
    root.mainloop()
```

In Python, there is no explicit `main` function. Instead when a script is run, all level 0 indentation is run as the `main` function. When the script is being run explictly, the formatting of `if __name__ == "__main__":` is unnecessary because the level 0 indentation will be run automatically. However, if we want to import a script into another, we may not want the main function of the imported script to interrupt or replace the main function of the desired script. For this reason, Python sets a special variable called `__name__` to `"__main__"` for the script that was called at the highest level. We can put our main functionality in the level of indentation directly below this equality check.

## Important custom modules
Let's break down what the pieces of the `main` function are.

``` root = tk.Tk() ```

We have already imported tkinter as `tk`. The function `Tk()` initalizes the tkinter interpreter and creates, displays, and returns a reference to the root window. 

``` root.mainloop() ``` will automatically update idle tasks and recall 'drawing' functions used to display your tkinter widgets.

Lastly, we must actually create the display (the bulk of the code) and create our entire application. I have wrapped all of this in a class called `Application` that accepts the root display as a parameter so that it knows where to display it's widgets. 

### Application class
Let's look closer at the Application class and what it entails.

The first part to be looked at is the (long) constructor. In Python, this is specified by calling the function `__init__`. Since this is a member function of the class, the first parameter is `self`. As mentioned before, the class ctor also accepts the root window which we will call `parent`. The majority of this function is used to create the widgets which only appears once on the application as a whole, aka the ones that are not part of the repeatable Stations. For example, the instructions as the top, the clear counter button, and the count itself all belong to the Application.

In tkinter, there are two parts to displaying a widget.

#### Initialization

The first part is what is explicitly done in the Application ctor, initialization. Each widget is instantiated and set to member variables by using the `self.` keyword. This is done so that these objects can be accessed in other member functions. Here is an example of such initialization.

```
self.clearCounter = tk.Button(self.buttonFrame, text = "Clear Counter", width = int(long_len / 2), bg = gridColor, height = 2, command = clearDevCounter)
```

Here we can see the tk `Button` class ctor being called. The specific documentation for each widget can be found [here](http://effbot.org/tkinterbook/tkinter-index.htm), however each one has a similar construction pattern.

The first parameter is almost always the parent of the widget (e.g. where it should be displayed). We have already create a frame that will display the buttons called `buttonFrame`, so we can pass that in as the parent. For the rest of the parameters, it is generally easier to pass by name since the list of parameters can often be long. We want to pass the text that will be displayed with our button, the width in characters, the background color, the height, and most importantly the `command` parameter. The command parameter is the function that will be performed as a callback to the button being pressed. 

The command function can be a [lambda function](https://www.programiz.com/python-programming/anonymous-function) similar to anonymous functions in Javascript (works well if response code is short) or can be called with the name of the function to be performed. In this case, we assign `command = clearDevCounter` where `clearDevCounter` is a function that puts `0` in the text file that is the count of the successful modules completed.

#### Display
After initializing each widget, we need some way to display the widget on it's parent. tkinter has two command geometry managers which are commonly used. The one used in this program is called `pack`. Generally, this manager is slightly easier to use than the other, which is called `grid`. However, `grid` can often be used for more complicated designs.

In order to use the pack manager, each widget needs to have the `.pack()` function called on itself. Without any parameters, the `pack` function will put widgets down the screen one after the other. However, this can be avoided by using several special parameters to the function.

For one example, consider if we wanted a line of widgets displayed horizontally across the page. This would not be possible without any parameters, because they would line up vertically. Here, the `side` parameter comes in handy. If we specify the side to which the widget should be displayed, then the manager will continue packing widgets with a priority to pack the object against a certain side. Take a look at the excerpt below.

```
self.titleLabel.pack()
self.instructions.pack()
self.can_label.pack(side = tk.LEFT)
if advanced.get():
    self.can_entry.pack(side = tk.LEFT)
self.deviceFrame.pack(side = tk.LEFT, padx = 10)
```

The titleLabel and instructions are both packed without parameters, meaning they will be displayed one after the other vertically, Next we want to display the can_label, can_entry, and the frame that holds the device specification on the same line. In order to do this, we specify that we want them packed on the left side of their parent. The widgets will continue packing on the same line (as far left as they can go) until another widgets is called without any parameters. 

Another useful parameter for the `pack` function is the pad parameters. This specifies how many pixels of x/y space you want between two widgets. Without any padding, the widgets sides touch and generally the space looks cramped.

Since all of this packing is done after initialization, I like to write a wrapper function that packs all of the objects in it. This way, if I want to change the design of the page, all I have to do is change how they are packed in that function.

Let's continue looking at the rest of the `Application` class now that we've seen how each tkinter wigets works.

The most important aspect of this class is the last two lines of the ctor.

```
 for d in range(1, len(devices)):
        self.stations.append(Station(root, devices[d][0], devices[d][1], self.can_com_text, self.mode, d))
```

Piece by piece of this excerpt:

* `devices` is a list of lists with the inner list detailing the COM ports (programming and serial communication) for each device to be programmed
* `devices[0]` is the common CAN communication port (*Note: Python lists can hold data of different types so `devices[0]` is a string but the rest of the items in `devices` are a list of strings*)
* `self.mode` is part of a feature that is not fully implemented; specifies whether program is in production or simple mode

In order to fully understand this, we need to discuss the `Station` class

## Station class
For many of the lab updating scripts, we want the main operation to be repeatable. For that reason, I often implemented a sepearte class handling all actions that should be reproducable. This allows for an easy way to instantiate multiple instances of the class. In the above example, we create a a `Station` using the ports specfied in the `devices` array, the CAN port it will be talking with, as well as a unique number to differentiate between each station (which is important in the communcation stage of the program). Each `Station` is added to an array tracking all of the Stations being programmed.

A closer look at the `Station` class will reveal many of the details seen in the functionality of the program.

First of all, let's look at the ctor in the same way we did for the `Application` class. The first line of the ctor says 

```
self.thread = threading.Thread(target = self.process)
```

This is saying that each Station has it's own thread that targets an action called `process`. Each process belongs to the Station which instantiated that thread. The process function starts and manages the execution of each step of the programming/verification process. By putting this series of events in it's own thread, we get a non-blocking behavior which we would not get by putting each Station's process in the same main thread. There are functions that manage the starting/resetting of each of these threads.

Next, there are some parts of this class that are data to be collected at some point through out the process. These include the serial number of the module (`self.sernum`), the version of the firmware that is being loaded (`self.version`), as well as failure indicators that are set after steps are performed.

Next, each of the ports specified by the parameters must be set up. The main serial port gets initialized as a Serial port which is imported through use of the pySerial library. 

Following this, we specify the tkinter widgets we need to display each Station's status, progress, and debug information. In a similar fasion to the Application class, this part of the process has it's own initialization and display steps.

Lastly, each step of the process is a member function within each Station. Functions like `self.configureTextFiles()`, `self.performFlashCommand()`, and `self.performVerification()` are member functions that perform the actions specific to each Station and then report back the results/status of those actions to be displayed to the user.
