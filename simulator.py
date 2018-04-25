'''
CS5250 Assignment 4, Scheduling policies simulator
Sample skeleton program
Author: Minh Ho
Input file:
    input.txt
Output files:
    FCFS.txt
    RR.txt
    SRTF.txt
    SJF.txt

Apr 10th Revision 1:
    Update FCFS implementation, fixed the bug when there are idle time slices between processes
    Thanks Huang Lung-Chen for pointing out
Revision 2:
    Change requirement for future_prediction SRTF => future_prediction shortest job first(SJF), the simpler non-preemptive version.
    Let initial guess = 5 time units.
    Thanks Lee Wei Ping for trying and pointing out the difficulty & ambiguity with future_prediction SRTF.
'''

import sys
import Queue
import heapq

input_file = 'input.txt'

class Process:
    last_scheduled_time = 0
    def __init__(self, id, arrive_time, burst_time):
        self.id = id
        self.arrive_time = arrive_time
        self.burst_time = burst_time
        self.unit_processed = 0

    def process(self):
        self.unit_processed = self.unit_processed + 1

    def is_done_processing(self):
        if self.unit_processed == self.burst_time:
            return True
        else:
            return False
    
    def reset_process(self):
        self.unit_processed = 0

    def has_arrived(self, current_time):
        if current_time == self.arrive_time:
            return True
        else:
            return False

    def getProcessCycleLeft(self):
        return self.burst_time - self.unit_processed

    #for printing purpose
    def __repr__(self):
        return ('[id %d : arrive_time %d,  burst_time %d]'%(self.id, self.arrive_time, self.burst_time))

class Processor:
    def __init__(self):
        self.current_executing_process = None
        self.predicted_burst_cache = None
        self.initial_burst_guess = None
        self.predicted_burst_alpha = None

    def init_predict(self, alpha, initial_guess):
        self.predicted_burst_cache = {}
        self.initial_burst_guess = initial_guess
        self.predicted_burst_alpha = alpha

    def get_predicted_burst_cycle(self, process_id):
        if process_id not in self.predicted_burst_cache:
            self.predicted_burst_cache[process_id] = self.initial_burst_guess
        else:
            return self.predicted_burst_cache[process_id]

    def update_predicted_burst_cycle(self,process):
        self.predicted_burst_cache[process.id] = self.predicted_burst_alpha*process.burst_time + (1-self.predicted_burst_alpha)*self.predicted_burst_cache[process.id]

    def execute(self):
        self.current_executing_process.process()

    def isIdle(self):
        if self.current_executing_process is None:
            return True
        else:
            return False

    def attach(self, process):
        self.current_executing_process = process

    def detatch(self):
        if not self.isIdle():
            ret_process = self.current_executing_process
            self.current_executing_process = None
            if self.predicted_burst_cache is not None:
                self.update_predicted_burst_cycle(ret_process)
            return ret_process

    def getProcessID(self):
        try:
            return self.current_executing_process.id
        except Exception as e:
            raise e
            return None

    def has_process_finished(self):
        if not self.isIdle():
            return self.current_executing_process.is_done_processing()
        else:
            return True

    def get_CPU_Cycle_Left(self):
        return self.current_executing_process.getProcessCycleLeft()

    def __repr__(self):
        if self.isIdle():
            return "No process"
        else:
            return ('[id %d : arrive_time %d,  burst_time %d, completed_time %d]'%(self.current_executing_process.id, self.current_executing_process.arrive_time, self.current_executing_process.burst_time, self.current_executing_process.unit_processed))

def FCFS_scheduling(process_list):
    #store the (switching time, proccess_id) pair
    schedule = []
    current_time = 0
    waiting_time = 0
    for process in process_list:
        if(current_time < process.arrive_time):
            current_time = process.arrive_time
        schedule.append((current_time,process.id))
        waiting_time = waiting_time + (current_time - process.arrive_time)
        current_time = current_time + process.burst_time
    average_waiting_time = waiting_time/float(len(process_list))
    return schedule, average_waiting_time

#Input: process_list, time_quantum (Positive Integer)
#Output_1 : Schedule list contains pairs of (time_stamp, proccess_id) indicating the time switching to that proccess_id
#Output_2 : Average Waiting Time

def is_simulator_done(process_list):
    for process in process_list:
        if process.is_done_processing():
            continue
        else:
            return False

    return True

def RR_scheduling(process_list, time_quantum ):

    # Prepare process for simulator
    for process in process_list:
        process.reset_process()

    schedule = []
    current_time = 0
    waiting_time = 0
    quantum_time = 0

    cpu = Processor()

    my_scheduler = Queue.Queue()

    while not is_simulator_done(process_list):
        # Putting process into the scheudler based on arrival time
        for process in process_list:
            if process.has_arrived(current_time):
                my_scheduler.put(process)

        # Check whether CPU is processing any process
        if not cpu.isIdle():
            cpu.execute();
            # Increase quantum time since CPU is working
            quantum_time = quantum_time + 1
        else:
            # Get from scheduler if there is any and start processing
            if not my_scheduler.empty():
                cpu.attach(my_scheduler.get())
                schedule.append((current_time, cpu.getProcessID()))
                cpu.execute()
                # Increase quantum time since CPU is working
                quantum_time = quantum_time + 1
            else:
                # Do nothing since there is no process in scheduler
                pass

        # Keep track of waiting time dpending on the queue size
        waiting_time = waiting_time + my_scheduler.qsize()

        # Check whether process is done or quantum is up
        if not cpu.isIdle():
            if cpu.has_process_finished():
                cpu.detatch()
                quantum_time = 0 

            if quantum_time == time_quantum: # Not done, put in scheduler again
                my_scheduler.put(cpu.detatch())
                quantum_time = 0

        current_time = current_time + 1
        

    average_waiting_time = waiting_time / float(len(process_list))

    return schedule, average_waiting_time

def SRTF_scheduling(process_list):
    # Prepare process for simulator
    for process in process_list:
        process.reset_process()

    schedule = []
    current_time = 0
    waiting_time = 0
    quantum_time = 0

    cpu = Processor()

    my_scheduler = []

    while not is_simulator_done(process_list):
        # Putting process into the scheduler based on the burst_time to get the shortest remaining time and then arrival time 
        # so that the response time would be more optimal rather than an old process have to wait in the scheduler
        for process in process_list:
            if process.has_arrived(current_time):
                heapq.heappush(my_scheduler,(process.burst_time,process.arrive_time,process))

        
        # Check whether CPU is processing any process
        if not cpu.isIdle():
            # Put cpu process into scheduler and pop again to get the next scheduler to work with
            process = cpu.detatch()
            heapq.heappush(my_scheduler,(process.getProcessCycleLeft(),process.arrive_time,process))
            cpu.attach(heapq.heappop(my_scheduler)[2])
            if process.id != cpu.getProcessID(): # Change in scheduling detected
                schedule.append((current_time, cpu.getProcessID()))
            cpu.execute()
        else:
            # Get from scheduler if there are any process and start processing
            if my_scheduler:
                cpu.attach(heapq.heappop(my_scheduler)[2])
                schedule.append((current_time, cpu.getProcessID()))
                cpu.execute()
            else:
                # Do nothing since there is no process in scheduler
                pass

        # Keep track of waiting time depending on the length of scheduler
        waiting_time = waiting_time + len(my_scheduler)

        # Check whether process is done 
        if not cpu.isIdle():
            if cpu.has_process_finished():
                cpu.detatch()

        current_time = current_time + 1
        

    average_waiting_time = waiting_time / float(len(process_list))

    return schedule, average_waiting_time

def SJF_scheduling(process_list, alpha):

    # Prepare process for simulator
    for process in process_list:
        process.reset_process()

    schedule = []
    current_time = 0
    waiting_time = 0
    quantum_time = 0

    initial_guess = 5

    cpu = Processor()
    cpu.init_predict(alpha, initial_guess)

    my_scheduler = []

    while not is_simulator_done(process_list):
        
        # Putting processor into the scheduler based on the predicted_burst_time and then followed by arrival time
        # so that the response time would be more optimal rather than an old process have to wait in the scheduler
        for process in process_list:
            if process.has_arrived(current_time):
                heapq.heappush(my_scheduler,(cpu.get_predicted_burst_cycle(process.id),process.arrive_time,process))

        # Check whether CPU is processing any process
        if not cpu.isIdle():
            # Continue Processing until end of work
            cpu.execute()
        else:
            # Get from scheduler if there are any process and start processing
            if my_scheduler:
                cpu.attach(heapq.heappop(my_scheduler)[2])
                schedule.append((current_time, cpu.getProcessID()))
                cpu.execute()
            else:
                # Do nothing since there is no process in scheduler
                pass

        # Keep track of waiting time depending on length of scheduler
        waiting_time = waiting_time + len(my_scheduler)

        # Check whether process is done
        if not cpu.isIdle():
            if cpu.has_process_finished():
                cpu.detatch()

        current_time = current_time + 1

    average_waiting_time = waiting_time / float(len(process_list))

    return schedule, average_waiting_time

def read_input():
    result = []
    with open(input_file) as f:
        for line in f:
            array = line.split()
            if (len(array)!= 3):
                print ("wrong input format")
                exit()
            result.append(Process(int(array[0]),int(array[1]),int(array[2])))
    return result
def write_output(file_name, schedule, avg_waiting_time):
    with open(file_name,'w') as f:
        for item in schedule:
            f.write(str(item) + '\n')
        f.write('average waiting time %.2f \n'%(avg_waiting_time))


def main(argv):
    process_list = read_input()
    print ("printing input ----")
    
    for process in process_list:
        print (process)
    
    print ("simulating FCFS ----")
    FCFS_schedule, FCFS_avg_waiting_time =  FCFS_scheduling(process_list)
    write_output('FCFS.txt', FCFS_schedule, FCFS_avg_waiting_time )
    
    print ("simulating RR ----")
    RR_schedule, RR_avg_waiting_time =  RR_scheduling(process_list,time_quantum = 2)
    write_output('RR.txt', RR_schedule, RR_avg_waiting_time )
    
    print ("simulating SRTF ----")
    SRTF_schedule, SRTF_avg_waiting_time =  SRTF_scheduling(process_list)
    write_output('SRTF.txt', SRTF_schedule, SRTF_avg_waiting_time )
    
    print ("simulating SJF ----")
    SJF_schedule, SJF_avg_waiting_time =  SJF_scheduling(process_list, alpha = 0.5)
    write_output('SJF.txt', SJF_schedule, SJF_avg_waiting_time )

if __name__ == '__main__':
    main(sys.argv[1:])