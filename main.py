from tkinter import *
import time
import boto3

class Window:
    def __init__(self, width, height):
        self.__root = Tk()
        self.__root.wm_title("AWS Instance Controller")
        self.__root.canvas = Canvas(width=width, height=height)
        self.__root.canvas.pack()
        self.__root.running = False
        self.__root.protocol("WM_DELETE_WINDOW", self.close)

    def redraw(self):
        self.__root.update_idletasks()
        self.__root.update()

    def wait_for_close(self):
        self.__root.running = True
        while self.__root.running == True:
            self.redraw()

    def close(self):
        self.__root.running = False

    def addText(self, instance):
        instance.createInstanceText(self.__root.canvas)
    
    def addControls(self, instance):
        instance.addInstanceControl(self.__root.canvas)

    def removeEntry(self, tag):
        self.__root.canvas.delete(tag)
        self.redraw()

class Instance:
    def __init__(self, win, id, name, status, previous_instance):
        self.win = win
        self.instance_id = id
        self.instance_name = name
        self.instance_status = status
        self.button = None
        if previous_instance == None:
            self.x = 250
        else:
            self.x = previous_instance.x
        if previous_instance == None:
            self.y = 50
        else:
            self.y = previous_instance.y+50

    def createInstanceText(self, canvas):
        if self.instance_status == "running":
            fill = "red"
        else:
            fill = "black"
        canvas.create_text(self.x, self.y, text=self.instance_id, fill="black", font=('Helvetica 15 bold'), tag=self.instance_id)
        canvas.create_text(self.x+400, self.y, text=self.instance_name, fill="black", font=('Helvetica 15 bold'), tag=self.instance_id)
        canvas.create_text(self.x+700, self.y, text=self.instance_status, fill=fill, font=('Helvetica 15 bold'), tag=self.instance_id)
        canvas.pack()

    def clearInstanceText(self, canvas):
        canvas.delete(self)
    
    def addInstanceControl(self, canvas):
        text = None
        if self.instance_status == "running":
                text = "Stop"
        if self.instance_status == "stopped":
            text = "Start"
        if self.instance_status == "stopping" or self.instance_status == "pending":
            text = "Please Wait"
        
        def instanceControl():
            if self.instance_status == "running":
                response = ec2.stop_instances(
                    InstanceIds=[self.instance_id]
                )
            if self.instance_status == "stopped":
                response = ec2.start_instances(
                    InstanceIds=[self.instance_id]
                )
            self.updateInstanceDisplay()        

        self.button = Button(canvas, text=text, command=instanceControl)
        self.button.place(x=self.x+800, y=self.y-10)
    
    def updateInstanceDisplay(self):
        print("updating...")
        time.sleep(1)
        updated_status = ec2.describe_instances(
            InstanceIds=[self.instance_id],
        )
        self.instance_status = updated_status['Reservations'][0]['Instances'][0]['State']['Name']
        print(self.instance_status)
        self.win.removeEntry(self.instance_id)
        self.win.addText(self)
        self.win.addControls(self)
        if self.instance_status == "stopping" or self.instance_status == "pending":
            self.updateInstanceDisplay()
        
ec2 = boto3.client('ec2')

instances = ec2.describe_instances(
    Filters=[
        {
            'Name':'tag:Service Channel',
            'Values': [
                'Staging',
                'Development',
                'staging',
                'development'
            ]
        },
    ],
)
    
awsApp = Window(1280, 720)

# Master instance list
instance_list = []

# Initial enumeration of instances. 
for instance in instances['Reservations']:
    name = None
    for value in instance['Instances'][0]['Tags']:
        if value['Key'] == "Name":
            name = value
    previous_instance = None
    if instances['Reservations'].index(instance)-1 >= 0:
        previous_instance = instance_list[instances['Reservations'].index(instance)-1]
    new_instance = Instance(
        awsApp,
        instance['Instances'][0]['InstanceId'], 
        name['Value'], 
        instance['Instances'][0]['State']['Name'],
        previous_instance
        )
    instance_list.append(new_instance)
    awsApp.addText(new_instance)
    awsApp.addControls(new_instance)
    # Printing to the CLI for backup  
    print(name['Value'])        
    print(instance['Instances'][0]['InstanceId'])
    print(instance['Instances'][0]['State']['Name'])

awsApp.wait_for_close()



