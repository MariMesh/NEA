import random
from enum import Enum
from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk

#creates an enum class that establishes three constants for each state
class States(Enum):
    SUSCEPTIBLE = 0
    INFECTED = 1
    RECOVERED = 2

# constant list of offsets that are used to access neighbour cells
NEIGHBOURS_OFFSET = [(-1, 1), (0, 1), (1, 1),
                     (-1,0), (1,0),
                     (-1,-1), (0,-1), (1,-1)]

#constant default settings
DEFAULT_HEIGHT = 25
DEFAULT_WIDTH = 25
DEFAULT_BETA = 0.4
DEFAULT_GAMMA = 0.1
DEFAULT_INFECTION_RATIO = 0.1
DEFAULT_MAX_TIME = 100

#colour map that maps each state to a colour
COLOUR_MAP: dict[States, str] = {
    States.SUSCEPTIBLE: "#3bd9f5",
    States.INFECTED:    "#f5473b",
    States.RECOVERED:   "#3bf57f",
}

#These are parameters for the GUI dimensions and the simulation running process
CELL_PIXEL_SIZE = 20
CANVAS_PADDING = 10
TIME_DELAY_MS = 150 # how much the simulation waits until updating, this is needed so you can see the changes

# ABC establishes Cell class as an abstract class(base class
class Cell(ABC):

    #: symbol after variable is a way to specify the data type, by doing that we self document and
    #   make it less likely there to be a logical error
    def __init__(self,row:int,col:int):
        #_ before the variable name means that the attribute is privet/protected
        self._row = row
        self._col = col
        """I decided to delete the time step attribute in the cell class. Since because the change of state now being executed by replacing the cell itself the time step in the cell class is unnecessary"""

    #-> after function is also a way to specify what the function returns, this self document the code making it more clear and
    #      readable and prevents logic errors

    # @property = Decorator used to determine a method as a property (it can be accessed like an attribute)
    #   Benefits:Add additional logic when read, write or delete attributes.
    #   Gives yoy getters, setter and deleter method.

    @property
    #getter for row
    def row(self)->int:
        return self._row

    @property
    #getter for column
    def col(self)->int:
        return self._col

    @property
    #getter for position, coordinates of the cell
    def position(self) -> tuple[int,int]:
        return self._row,self._col

    #getter for state that will be overridden in the child classes
    @property
    @abstractmethod
    def state(self) -> States:
        pass

    #method that will do the maths about updating the cell
    #->"Cell" means that it will return an object of one of the cell classes
    @abstractmethod
    def update(self,infected_neighbour_count:int,beta:float,gamma:float)->"Cell":
        pass
    #infected_neighbour_count is the number of infected neighbours
    #beta - B value and gamma - y value that are specified to be floats

#(Cell) means that this class inherits from the Cell class
class SusceptibleCell(Cell):

    #returns State constant based on the cell state
    @property
    def state(self) -> States:
        return States.SUSCEPTIBLE

    def update(self, infected_neighbour_count: int, beta: float, gamma: float) -> Cell:
        #checks if the infected_neighbour_count is invalid, if yes, it raises a value error telling that it is the case
        if infected_neighbour_count < 0:
            raise ValueError("infected_neighbour_count cannot be negative")

        #if there is no infected neighbours it just returns itself because the state did not change
        if infected_neighbour_count == 0:
            return self

        """This method is better method of calculation the chance because it is now relative to the number of infected neighbours of the cell"""
        # probability of avoiding getting infected,
        #   probability of not getting infected to the power of the number of infected neighbours - this way it decreases with each neighbour
        escape_chance = (1.0-beta)**infected_neighbour_count

        #random.random() generates a real number between 1 and 0
        #if it is greater than escape chance then the cell gets infected
        if random.random() > escape_chance:
            return InfectedCell(self._row,self._col)
        #else nothing happens and it returns itself
        return self


class InfectedCell(Cell):

    @property
    def state(self) -> States:
        return States.INFECTED

    def update(self,infected_neighbour_count:int,beta:float,gamma:float) ->Cell:

        #if a real between 1 and 0 is greater than gamma the cell successfully recovers
        """The gamma partially did not work in the prototype due to the fact that it could be more than one. So for the purposes of this model the math got changed.
        Because when it was greater or equals to 1 it would guaranty the recovery"""
        if random.random() > gamma:
            return RecoveredCell(self._row, self._col)

        return self


class RecoveredCell(Cell):

    @property
    def state(self) -> States:
        return States.RECOVERED

    #because the recovered state is the end state for the SIR model it just returns itself
    def update(self,infected_neighbour_count:int,beta:float,gamma:float) -> Cell:
        return self

class Record:
    def __init__(self,time_step:int,susceptible:int,infected:int,recovered:int):
        #records the time step
        self._time_step = time_step
        # These attributes have counter for each state
        self._susceptible = susceptible
        self._infected = infected
        self._recovered = recovered

    #getter for time step
    @property
    def time_step(self) -> int:
        return self._time_step

    #getter for the number of susceptible cells
    @property
    def susceptible(self) -> int:
        return self._susceptible

    # getter for the number of infected cells
    @property
    def infected(self) -> int:
        return self._infected

    # getter for the number of recovered cells
    @property
    def recovered(self) -> int:
        return self._recovered

    #getter for the total number of cells
    @property
    def total(self) ->int:
        return self.susceptible + self.infected + self.recovered

    #creates and returns a dictionary {key:state,value:number of cells with that state}
    #this makes this data easy to accessible for analytics
    def get_dict(self) -> dict[str, int]:
        return {"susceptible":self.susceptible,
                "infected":self.infected,
                "recovered":self.recovered}


"""Merge sort is a sorting algorithm that can sort lists by continuously taking it apart until each element is separate and then by putting them back together in order, one by one. 
It is most efficient sorting algorithm to use on big lists. This is why it can be extremely useful to sort records for this project."""
def merge_sort(items:list, key=None, reverse:bool =False) -> list:
    #This checks whether the list is empty or doesn't need to be sorted or decided any further(has only one element)
    if len(items) <= 1:
        return items

    # A lambda function is a small anonymous function.A lambda function can take any number of arguments, but can only have one expression.
    # So if the key have not been inputted then the key is assigned with a lambda expression
    """By using the key as lambda we can easily access parameter of records when searching
        e.g. lambda record:record.time_step would be inputted with the record and will accesses the time step
        Because we can input the key we can use the merge sort for multiple aspects"""
    if key is None:
        key = lambda x:x

    # we calculate mid-point of the list using integer division(there is no remainder)
    mid_point = len(items) // 2

    # Then according to the mid-point we divide the list into two, left(items[:midpoint]) and right(items[midpoint:]).
    # Using this as one of the inputs for merge sort function. This makes use of recursion, it is when the function calls itself with in itself.
    left = merge_sort(items[:mid_point], key=key, reverse=reverse)
    right = merge_sort(items[mid_point:], key=key, reverse=reverse)

    # Then it returns the results of merged function. This makes this function nested because it calls another function it itself.
    return _merge(left, right,key=key, reverse=reverse)

def _merge (left:list, right:list,key,reverse:bool) -> list:
    #creates an instance of left index, right index and merged list
    left_index = 0
    right_index = 0
    merged_list = []

    # while the left and right index is smaller than the length of the lists respectively
    # this way we will go thought the lists' elements one by one
    while left_index < len(left) and right_index < len(right):
        #these values store the elements that will be compared accessed through the
        left_value = key(left[left_index])
        right_value = key(right[right_index])

        # depending on weather the order we decide weather or not left value should go first in the sequence
        if reverse:
            take_left = left_value >= right_value
        else:
            take_left = left_value <= right_value
        #depending on the results we add the value to the merge list and increment the relevant index
        if take_left:
            merged_list.append(left[left_index])
            left_index += 1
        else:
            merged_list.append(right[right_index])
            right_index += 1

    # extend() - Extend list by appending elements from the iterable. How it differentiates from append is by the fact that you can add more than one element at a time.
    # Then we add to merge:
    # elements from the left list that are to the right of the left index
    # elements from the right list that are to the right of the right index
    # this way the leftover elements get added
    merged_list.extend(right[right_index:])
    merged_list.extend(left[left_index:])
    # The merged and sorted list is then returned
    return merged_list

"""Binary search is an algorithm that searches a list by compering the middle value to the target and descanting the not reverent half of the list and repeating the process until the target was found. 
It is an efficient search algorithm for bigger lists, which makes it very useful for searching through records for analytics"""
def record_step_bs(sorted_records:list[Record], target_step:int) -> Record:#bs => binary search
    # creates low and height pointers: low-o and high - length of the sorted list minus one
    """These pointers are showing the limit of the list that we are looking at, at the time"""
    low=0
    high= len(sorted_records) - 1
    # while the low pointer is less than or equal to high pointer
    """So this will stop if low or high will get out of range or the search comes down to only one value, therefor if the target element was not found"""
    while low<=high:
        # calculates the mid-point from the sum of pointers
        mid_point = (low+high)//2
        # it gets the time_step of the record in the mid_point of the list and stores it as a value
        mid_step = sorted_records[mid_point].time_step
        # it checks whether the mid_step is our value
        if mid_step == target_step:
            # if that is the case it returns the record
            return sorted_records[mid_point]
        # if middle step is lesser then target
        elif mid_step < target_step:
            # low became mid + 1
            low = mid_point+1
        else:
            # high became mid -1
            high = mid_point-1
        """This way half of the list gets discarded with every cycle of the search"""
    #If the wile loop run out the target is not in the list, so we raise value error
    raise ValueError(f"{target_step} time step must not be in the record list")


class SimAnalytics:
    def __init__(self):
        #SimAnalytics is a container class for records
        #Simulation history will store the records and be accessed for analytics
        self._sim_history:list[Record] = []

    #getter for the whole history
    @property
    def sim_history(self) -> list[Record]:
        return self._sim_history

    #getter for the length of the histor- how menu steps were taken
    @property
    def step_count(self) -> int:
        return len(self.sim_history)

    #This record a new record in current step
    def record_new_step(self,time_step:int,state_counts:dict[States,int]) -> None:#state_counts:dict is a dictionary with all state counts
        #creates a new record
        record = Record(
            time_step,
            state_counts[States.SUSCEPTIBLE],
            state_counts[States.INFECTED],
            state_counts[States.RECOVERED]
        )
        #adds the new record to history
        self._sim_history.append(record)

    #removes last record
    def delete_last(self)->None:
        #cheaks if the history is empty
        if self._sim_history:
            #using pop() we can remove last record from the list
            self._sim_history.pop()

    #This method returns the total number of cells that have been infected previously at a certain step
    def cumulative_infection_sum(self,step:int) -> int:
        #This checks if the step is in range of history list, this prevents logic errors
        if step < 0 or step > (len(self._sim_history)-1):
            raise ValueError("step must be between 0 and the total number of records in history")
        # this gets the record at the inputted step
        selected_record = self.find_record_by_step(step)
        #Then we output sum of infected and recovered cells from that record
        return selected_record.infected + selected_record.recovered

    #this method estimates r0 of the simulation
    """Due to the change in maths with gamma and beta we now calculate r0 by rate of change."""
    def r0_estimate(self,) -> float:
        #Cheaks if the history is long enough to get an estimate
        if len(self._sim_history) < 3:
            #If not it returns 0
            return 0.0

        #creates a list where we will be storing the growth ratios of the infection
        growth_ratios =[]
        # This for loop makes minimum the length of history max 10 loops(really 9 loops because it starts at 1)
        # So it will go through history or 9 record to get an estimate
        for step in range(1,min((len(self._sim_history)-1),10)):
            # we store values of previous and current infection numbers in separate values
            previous_infected = self._sim_history[step-1].infected
            current_infected = self._sim_history[step].infected
            #we check if the previous step had any infected cells because we can not divide by 0.
            if previous_infected > 0:
                #we calculate ratio of change
                ratio = current_infected/previous_infected
                #then we add it to the list
                growth_ratios.append(ratio)
        #if the list is empty we return zero
        if not growth_ratios:
            return 0.0
        #we get an average growth ratio that will act as our r0 value
        average_growth_ratio = sum(growth_ratios) / len(growth_ratios)
        return round(average_growth_ratio,3)#we round before returning

    #this method returns the record at particular time step
    def find_record_by_step(self,step:int) -> Record:
        #merge_sort(self._sim_history, key=lambda record:record.time_step) - puts history in order according to time_step
        #record_step_bs() finds the record with that time step
        return record_step_bs(merge_sort(self._sim_history, key=lambda record:record.time_step),step)

    #This method gets a record with the biggest number of infected cells
    def find_peak_infection(self)->Record:
        #cheaks whether history exists and has elements
        if not self._sim_history:
            #if not we raise a value error
            raise ValueError("No simulation history")
        #merge_sort(self._sim_history, key=lambda record:record.infected, reverse=True) sorts by infection in descending order
        history_by_infection = merge_sort(self._sim_history, key=lambda record:record.infected, reverse=True)
        return history_by_infection[0] #we return first element in the list

    #summery is a method that returns analytics
    @property
    def summery(self) -> dict:
        #cheaks if history exists or is empty
        if not self._sim_history:
            #if so it raises an error
            raise ValueError("No simulation history")
        #gets record with the highest infection and the last time step
        last_step = len(self._sim_history)-1
        peak_infection = self.find_peak_infection()
        #returns analytics as a dictionary
        return {
            "peak_infection time": peak_infection.time_step,
            "r0_estimate":self.r0_estimate(),
            "final record":self._sim_history[last_step],
            "total_infected":self.cumulative_infection_sum(last_step)
        }



class Grid:
    def __init__(self, height:int, width:int):
        # if the input is invalid then it raises a value error
        if height < 1 or width < 1:
            raise ValueError("Grid dimensions must be positive integers.")
        # assigns the privet variables
        self._height = height
        self._width = width

        # creates a 2D list that is filed with cell objects: susceptible cells
        # self._cells: list[list[Cell]] -> defines the data type used
        self._cells:list[list[Cell]] = [ [SusceptibleCell(row,col) for row in range(height) ] for col in range(width)]

        # a dictionary that stores cell coordinat and coordinates of the adjacent cells - {key:cell coordinates,value:list of neighbour cell coordinates}
        self._adjacent_cells:dict[tuple[int,int],list[tuple]] = {}
        #we call a privet method to build the dictionary
        self._build_adjacent_dict()

    #getter for height
    @property
    def height(self)->int:
        return self._height

    #getter for width
    @property
    def width(self)->int:
        return self._width

    #getter for the total number of cells
    @property
    def total_cells(self)->int:
        return self._height*self._width

    #getter for cell specified by coordinates
    def get_cell(self,row:int,col:int)->Cell:
        #cheaks whether the coordinates are out of range
        if row < 0 or row >= self._height or col < 0 or col >= self._width:
            raise IndexError("coordinates are out of bounds")
        #returns cell at the position specified
        return self._cells[row][col]

    #method that build the adjacency dictionary
    def _build_adjacent_dict(self)->None:
        #loops through the grid
        for row in range(self._height):
            for col in range(self._width):
                # creates an instance of neighbour list
                neighbours:list[tuple] = []
                # for each tuple in NEIGHBOUR_OFFSETS:(d_row, d_col)
                for x_off, y_off in NEIGHBOURS_OFFSET:
                    # calculates the coordinates of the neighbours, using the % to have it looping around
                    neighbour_x = (row + x_off)%self._height
                    neighbour_y = (col + y_off)%self._width
                    # adds the result to the neighbour list
                    neighbours.append((neighbour_x,neighbour_y))

                self._adjacent_cells[(row,col)] = neighbours # assigns the value:(neighbour list) to the key:the cell

    #setter for cells, it sets inputted cell into specified position
    def set_cell(self,row:int,col:int,cell:Cell)->None:
        #cheaks whether the coordinates are out of range
        if row < 0 or row >= self._height or col < 0 or col >= self._width:
            raise IndexError("coordinates are out of bounds")
        #inserts the cell into the position
        self._cells[row][col] = cell

    #getter for neighbour cells
    def get_neighbours(self,row:int,col:int)->list[Cell]:
        return[
            self._cells[r][c] for r,c in self._adjacent_cells[(row,col)]#returns a list with cells from specified coordinates from the adjacency dictionary
        ]

    #returns the number of neighbouring infected cells
    def infected_neighbours_count(self, row:int, col:int)->int:
        return sum (
            #makea a list with ones for each infected cells then using sum() we add them up and return it
            1 for cell in self.get_neighbours(row,col)
            if cell.state == States.INFECTED
        )

    #infects the grid based on the q value(proportion)
    def seed_infection(self, proportion:float)->int:
        #cheaks if proportion is out of range
        """it can not be negative because there can not be negative amount of infected cells, and it can not be greater than 1 because it would mean more than 100% of cells are infected."""
        if not(0.0 <= proportion <= 1.0):
            raise ValueError("proportion must be between 0 and 1")

        #calculates the number of cells that will be infected
        infection_target = max(1,int(self.total_cells * proportion))
        #we generate a list of all coordinates
        coordinates = [(r,c) for r in range(self._height) for c in range(self._width)]
        #Then using random.shuffle() we put them in random sequence
        random.shuffle(coordinates)

        #then store the needed amount of coordinates in a separate value as a list
        selected_cells = coordinates[:infection_target]

        #for each position in the list we infect the cell
        for r,c in selected_cells:
            self._cells[r][c]= InfectedCell(r,c)

        #then we return the number of infected cells
        return infection_target

    #gets a list of all cells with the selected state
    def get_cells_by_state(self,waned_state:States)->list[Cell]:
        return [self._cells[r][c] for r in range(self._height) for c in range(self._width) if self._cells[r][c].state == waned_state]

    def count_by_state(self)->dict[States,int]:
        #a dictionary is created that stores the count for each state - {key:state in States,value:count}
        #This way we can easily add things up and then access the data
        counts: dict[States, int] = {state:0 for state in States}
        #loop through the grid
        for row in range(self._height):
            for col in range(self._width):
                #adds a 1 to the count value of the relevant state key
                counts[self._cells[row][col].state] += 1
        #returns the dictionary
        return counts

    """The yield keyword turns a function into a function generator.
            The function generator returns an iterator.
            The code inside the function is not executed when they are first called, but are divided into steps, one step for each yield, and each step is only executed when iterated upon.
            Unlike the return keyword which stops further execution of the function, the yield keyword returns the result so far, and continues to the next step.
            The return value will be a list of values, one item for each yield."""
    def iterate_coordinates(self):
        for row in range(self._height):
            for col in range(self._width):
                #outputs all positions one by one
                yield row,col

    #this method returns a 2D list filled with the states
    """This method would allow to easily recreate the grid in terms of its state arrangement"""
    def state_snapshot (self)-> list[list[States]]:
        #[[self._cells[r][c].state for r in range(self._height)] for c in range(self._width)] generates a list of states
        return [[self._cells[r][c].state for r in range(self._height)] for c in range(self._width)]

    #This method restores the grid from the previous snapshot
    def restore_snapshot(self,prev_snapshot:list[list[States]])->None:
        #loops through the grid
        for row in range(self._height):
            for col in range(self._width):
                #if the cells in the grid is not already the needed state
                if self._cells[row][col].state != prev_snapshot[row][col]:
                    #we insert a cell with a new cell that has the needed state
                    self._cells[row][col] = self._gen_cell_by_state(state=prev_snapshot[row][col],row=row,col=col)

    #This method returns a cell of the state inputted
    def _gen_cell_by_state(self,state:States,row:int,col:int)->Cell:
        #Cheaks weather the coordinates are in range of the grid
        if row < 0 or row >= self._height and col < 0 or col >= self._width:
            raise IndexError("coordinates are out of bounds")

        #returns cell of the state inputted
        if state == States.SUSCEPTIBLE:
            return SusceptibleCell(row, col)
        elif state == States.INFECTED:
            return InfectedCell(row,col)
        else:
            return RecoveredCell(row,col)


"""Stack is a FILO data structure that is used to store values.FILO means First In Last Out, this means that elements that were added firsts will be taken last from the data structure"""
"""We will be using it to store data about each step that can be used to restore that step, this allows to implement the undo feature of the simulation"""
class Stack:
    def __init__(self)->None:
        #the stack will be storing a list of tuples, each tuple stores[step:int,snapshot:list[list[States]], and is simulation complete: bool] of every step
        """This data will be used in case if a step needs to be undone, by using FILO data structure we can easily remove the top element that will store data on the last step"""
        self._stack:list[tuple[int,list[list[States]],bool]] = []

    #getter for the length of the stack
    @property
    def size(self)->int:
        return len(self._stack)

    #This checks if the stack is empty. By checking if the stack is empty before operating on it, we can avoid errors.
    @property
    def is_empty(self)->bool:
        return len(self._stack) == 0

    #removes and returns the top element of the stack
    def pop (self):
        #pop() removes and returns the top element of the list
        return self._stack.pop()

    # adds an element to the top of the stack
    def push (self, items:tuple[int,list[list[States]],bool])->None:
        self._stack.append(items)

    #returns the top element of the stack, it is called peek because we're only "looking" at it and not removing it
    def peek (self):
        return self._stack[-1]

    #this clears the stack
    def clear (self)->None:
        self._stack.clear()

    #returns the stack
    @property
    def stack_list(self)->list:
        return self._stack

class Simulation:

    def __init__(self,height:int,width:int,beta:float,gamma:float,max_time:int,initial_infection_ratio:float):
        #these checks are the inputs in range or are valid
        if height < 1 or width < 1:
            raise ValueError("Size parameters are out of range, height and width have to be greater than 1")
        if not(0.0 <= beta <= 1.0):
            raise ValueError("Beta must be between 0 and 1")
        if not(0.0 <= gamma <= 1.0):
            raise ValueError("Gamma must be between 0 and 1")
        if max_time < 1:
            raise ValueError("max_time must be greater than 1")
        if not(0.0 <= initial_infection_ratio <= 1.0):
            raise ValueError("infection ratio must be between 0 and 1")

        #Makes the essential attributes of the simulation: B,y,q,T and t
        self._beta = beta#B
        self._gamma = gamma#y
        self._infection_ratio = initial_infection_ratio#q
        self._max_time = max_time#T
        self._current_time_step = 0#t

        #This attributes stores a boolean that corresponds to whether the simulation is complete or not
        self._complete = False

        #Creates instances of grid, analytics and stack class
        self._grid:Grid = Grid(height,width)
        self._analytics:SimAnalytics= SimAnalytics()
        self._undo_stack:Stack = Stack()

        self.grid.seed_infection(initial_infection_ratio)

    #getter for beta
    @property
    def beta(self)->float:
        return self._beta

    #getter for gamma
    @property
    def gamma(self)->float:
        return self._gamma

    #getter for T value - the max amount of time the simulation can run for
    @property
    def max_time(self)->int:
        return self._max_time

    #getter for current time step
    @property
    def current_time_step(self)->int:
        return self._current_time_step

    #this method answers whether the simulation is complete
    @property
    def complete(self)->bool:
        return self._complete

    #getter for the grid
    @property
    def grid(self)->Grid:
        return self._grid

    #getter for the simulation analytics
    @property
    def analytics(self)->SimAnalytics:
        return self._analytics

    #this method returns dictionary with all parameters of the simulation
    @property
    def parameters(self) -> dict:
        return {
            "beta":self._beta,
            "gamma":self._gamma,
            "max_time":self._max_time,
            "current_time_step":self._current_time_step,
            "complete":self._complete,
            "grid":self._grid,
            "analytics":self._analytics
        }

    #cheaks whether we can undo a step of the simulation - if the undo stack is not empty
    @property
    def can_undo(self)->bool:
        return not self._undo_stack.is_empty

    #this method undoes a step
    def undo(self)->bool:
        #cheaks if there is a step to go back to
        if self._undo_stack.is_empty:
            """The boolean corresponds to whether we have/could undo a step"""
            return False

        #stores the data into values
        prev_time_step,prev_snapshot,prev_complete = self._undo_stack.pop()

        #restores the previous step
        self._current_time_step = prev_time_step
        self._grid.restore_snapshot(prev_snapshot)
        self._complete = prev_complete
        #delits the last record of the step that we have undone
        self._analytics.delete_last()

        return True

    #this method records the new step
    def _record_new_step(self)->None:
        #getts dictionary of the states
        counts = self._grid.count_by_state()
        #records a new record into analytics
        self._analytics.record_new_step(self._current_time_step,counts)

    # this method updates the simulation - evidences to the next step
    def simulation_update(self) -> bool:
        #cheaks if the simulation is complete, if the case we do not need to preside with update
        if self._complete:
            """The out put will signify whether the simulation has stoped running"""
            return False

        #we add data about the previous step into the undo stack before updating it - so in case we would need to undo and come back to the previous step
        self._undo_stack.push(
            (self._current_time_step,self._grid.state_snapshot(),self._complete)
        )
        #increments current time step
        self._current_time_step += 1
        #This list will store new cells and their coordinates if the state have changed
        change_state:list[tuple[int,int,Cell]] = []
        #we go through all the positions in the grid
        for r,c in self._grid.iterate_coordinates():
            #getting the cell at the positon that we are looking at
            cell = self._grid.get_cell(r,c)
            #we update the cell and store it as a new cell.
            new_cell = cell.update(infected_neighbour_count= self._grid.infected_neighbours_count(r,c),beta=self._beta,gamma= self._gamma)
            #if the new cell is not the same cell as the previous cell - this means that the cell has change state
            if cell != new_cell:
                #we add it and its position to the list
                change_state.append((r,c,new_cell))
        #we go through the list of changed cell and replace the old cells
        for r,c,cell in change_state:
            self._grid.set_cell(r,c,cell)
        #we record the cord the changes in a new record
        self._record_new_step()

        #get the state dictionary
        counts = self._grid.count_by_state()
        #if the total number of infected cells is zero the simulation is complete
        if counts[States.INFECTED] == 0:
            self._complete = True
            return False
        #if the simulation has reached the max time it is complete
        elif self._max_time == self._current_time_step:
            self._complete = True
            return False
        #otherwise the simulation is still running
        else:
            return True

    #this method runs the simulation until it is completed and then returns the summery
    def run_until_complete(self)->dict:
        while self.simulation_update():
            pass
        return self._analytics.summery


class SimulationGUI:
    def __init__(self):
        self._simulation:Simulation|None = None
        self._running:bool = False
        #this is a variable that we will use to crate time delay or more specifically canceling of the time delay
        self._id_animation = None

        #creating the window
        self._root = tk.Tk()
        #giving the wind a title
        self._root.title("Virus Simulation NEA Project")
        #make it so the window can not be resized
        self._root.resizable(False,False)

        #bild the interface
        self._build_parameter_frame()
        self._build_control_frame()
        self._build_grid_canvas()
        self._build_statistics_frame()

    #This method builds the parameter frame of the interface, and build entry dictionary
    def _build_parameter_frame(self)->None:
        # creates a labeled frame in the window labeled parameters with size 8
        frame = ttk.LabelFrame(self._root, text="Parameters",padding=8)

        # grid(): Arranges widgets in rows and columns and further things such as:
        """column span=number - this widget will span several columns
            pad x=amount - add padding in x direction 
            pad y=amount - add padding in y direction
            sticky = specifies where it positions itself or it sticks to 
                - eg sticky="w"  means stick to the right 
                - eg sticky="e"  means stick to the left """

        frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="w")

        """After this we create lists that will be then used to create the enter widgets. 
        Enter widgets is where the user will be able to enter a line of text as an input and update them when needed"""

        # this makes a list of the labels for the batons for the frame
        labels = ["Height:", "Beta (\u03b2):", "Initial Infected:",
                  "Width:", "Gamma (\u03b3):", "Max Time:"]
        # makes a list of default variables that will be inserted as the starting point for the user
        defaults = [str(DEFAULT_HEIGHT), str(DEFAULT_BETA), str(DEFAULT_INFECTION_RATIO),
                    str(DEFAULT_WIDTH), str(DEFAULT_GAMMA), str(DEFAULT_MAX_TIME)]
        #we make list of keys that correspond each value this would allow us to update the entries when needed
        keys = ["height","beta","initial_infection",
                "width","gamma","max_time"]

        #we will store each entry with corresponding key in this dictionary to access later
        self._parameter_entries:dict[str,ttk.Entry] = {}

        # enumerate() - allows to loop through the index and elements in the same time
        # zip()- combines multiple iterables (like lists, tuples , sets etc.) into one iterable
        for index, (label_text, default,key) in enumerate(
                zip(labels, defaults,keys)):
            # we make the label for the widget and position it on the grid
            ttk.Label(frame, text=label_text).grid(
                #row=index // 3 - makes sure that when the index reaches 3 it will start to put them on the next row
                #column=(index % 3) - makes it re set counting every third index and
                # *2 we skip every two so {0,2,4,0,2,4} - this leaves enough space for the entry widgets
                row=index // 3, column=(index % 3) * 2,
                padx=4, pady=2, sticky="e"
                # sticky="e" makes it stick to the left
                # pad x and y determine the size of the x and y dimensions
            )

            # creates an Entry widget that is used to accept single-line text input from the user
            entry = ttk.Entry(frame, width=8)
            # Inserts default values into the entry
            entry.insert(0, default)
            # positions the entry widget on the grid
            entry.grid(
                #we add 1 to the column so it is to the side of the label and sticky="w" makes it stick to it
                row=index // 3, column=(index % 3) * 2 + 1,
                padx=4, pady=2, sticky="w"
            )
            #accigns entry to a key
            self._parameter_entries[key] = entry

    # This method builds the frame for controls of the interface
    def _build_control_frame(self)->None:
        #creating a labeled frame for controls
        frame = ttk.LabelFrame(self._root, text="Controls", padding=4)
        #row = 1 positions it bellow the parameter but in the same column
        frame.grid(row=1, column=0, columnspan=3,
                   padx=10, pady=8, sticky="w")

        self._start_button = ttk.Button(frame, text="Start",command=self._on_start)
        self._start_button.grid(row=0, column=0, padx=10, pady=10)

        self._reset_button = ttk.Button(frame, text="Reset", command=self._on_reset)
        self._reset_button.grid(row=0, column=1, padx=10, pady=10)

    #This method creates a canvas that we will bild our grid on
    def _build_grid_canvas (self) -> None:
        #we calculate the width and height for the canvas
        #DEFAULT_WIDTH/HEIGHT * CELL_PIXEL_SIZE
        width = (( DEFAULT_WIDTH * CELL_PIXEL_SIZE ) + 2 * CANVAS_PADDING)
        height = (( DEFAULT_HEIGHT * CELL_PIXEL_SIZE ) + 2 * CANVAS_PADDING)

        #we create a canvas attribute
        self._canvas = tk.Canvas(self._root, width=width, height=height, bg="white")

        #then we position it on the grid bellow the controls
        self._canvas.grid(row=2, column=0, padx=10, pady=10)

    #this method resizes the canvas in the scenario when the size of the grid was changed by the user
    def _resize_canvas(self, height:int, width:int) -> None:
        #we recalculate height and width of the canvas
        canvas_height = ((height * CELL_PIXEL_SIZE) + 2 * CANVAS_PADDING)
        canvas_width = ((width * CELL_PIXEL_SIZE) + 2 * CANVAS_PADDING)
        #then we change the height and width of the canvas
        self._canvas.config(height=canvas_height)
        self._canvas.config(width=canvas_width)

    #This method creates the statistics frame and sets up the labels
    def _build_statistics_frame(self)->None:
        #creating a Labeled frame for the statistics
        frame = ttk.LabelFrame(self._root, text="Statistics", padding=10)
        #positioning it on the grid of the window
        frame.grid(row=3, column=0, columnspan=3,sticky="w")

        #then we can create a labeled for each piece of statistics
        self._step = ttk.Label(frame, text="Step: 0")
        self._step.grid(row=1, column=0, padx=8, sticky="w" )

        self._susceptible = ttk.Label(frame, text="Susceptible: -")
        self._susceptible.grid(row=0, column=0, padx=8, sticky="w")

        self._infected = ttk.Label(frame, text="Infected: -")
        self._infected.grid(row=0, column=1, padx=8, sticky="w")

        self._recovered = ttk.Label(frame, text="Recovered: -")
        self._recovered.grid(row=0, column=2, padx=8, sticky="w")

        self._r0 = ttk.Label(frame, text="R\u2080: -")
        self._r0.grid(row=1, column=1, padx=8, sticky="w")

        self._satus = ttk.Label(frame, text="Sim. Satus: -")
        self._satus.grid(row=1, column=2, padx=8, sticky="w")

    def _update_statistics(self)->None:
        #we get the analytics object, attribute from the simulation object
        analytics:SimAnalytics = self._simulation.analytics

        #if the simulation haven't started and there is no stats that need to be updated and we exit
        if analytics.step_count == 0:
            return

        #we get the most recent record from the analytics object
        last_record = analytics.sim_history[-1]

        #we configure the labels from the statistics to reflect the updated statistics
        self._step.configure(text=f"Step: {analytics.step_count}")
        self._susceptible.configure(text=f"Susceptible: {last_record.susceptible}")
        self._infected.configure(text=f"Infected: {last_record.infected}")
        self._recovered.configure(text=f"Recovered: {last_record.recovered}")

        est_r0 = analytics.r0_estimate()
        self._r0.configure(text=f"R\u2080: {est_r0}")

    def _render_grid(self)->None:
        #we make sure that the canvas is reset
        self._canvas.delete("all")
        #we get the grid object from the simulation to make it easier to address
        grid = self._simulation.grid

        #we go through all the positions with the iterative function
        for row, col in grid.iterate_coordinates():
            #we get the cell at that position
            cell = grid.get_cell(row, col)
            #getts the corresponding colour from the colour map
            colour = COLOUR_MAP[cell.state]

            #we calculate x and y coordinates for each corner of the cell - to later render it as a rectangle
            x_0: int = CANVAS_PADDING + col * CELL_PIXEL_SIZE
            y_0: int = CANVAS_PADDING + row * CELL_PIXEL_SIZE
            x_1: int = x_0 + CELL_PIXEL_SIZE
            y_1: int = y_0 + CELL_PIXEL_SIZE
            #we create a rectangle that will represent the cell and its state
            self._canvas.create_rectangle(x_0, y_0, x_1, y_1, fill=colour, outline="#7a7a7a", width=1)

    #this inserts the inputted parameters
    def _populate_entries(self, parameters: dict[str, tk.Entry]) -> None:
        for key, entry in self._parameter_entries.items():
            if key in parameters:
                entry.delete(0, tk.END)
                entry.insert(0,str(parameters[key]))

    # this method reads parameters inputted by the user and outputs them as a dictionary that can be then used to create new simulation
    def _read_parameters(self) -> dict[str,int|float]:
        try:
            # we get each parameter from the dictionary with the corresponding key
            height = int(self._parameter_entries["height"].get())
            width = int(self._parameter_entries["width"].get())
            beta = float(self._parameter_entries["beta"].get())
            gamma = float(self._parameter_entries["gamma"].get())
            initial_infection =float(self._parameter_entries["initial_infection"].get())
            max_time = int(self._parameter_entries["max_time"].get())
        except ValueError:# if any of these values in the dictionary are errors
            raise ValueError("Parameter must be valid numbers.")

        #we check if the values are in range
        if (height <= 0 or width <= 0) or (height >= 100 or width >= 100):
            raise ValueError("Height and width must be less then 0 and must not be greater then 100.")
        if not 0.0 <= beta <= 1.0:
            raise ValueError("Beta must be between 0 and 1.")
        if not 0.0 <= gamma <= 1.0:
            raise ValueError("Gamma must be between 0 and 1.")
        if not 0.0 <= initial_infection <= 1.0:
            raise ValueError("Initial infection must be between 0 and 1.")
        if max_time < 1:
            raise ValueError("Max time must be greater than 0.")

        #after that we can now put it in the dictionary
        return {
            "height": height,
            "width": width,
            "beta": beta,
            "gamma": gamma,
            "max_time": max_time,
            "initial_infection_ratio": initial_infection
        }

    # the start button command
    def _on_start(self) -> None:
        #if the simulation was reset or haven't been started we create a new simulation
        if self._simulation is None:
            try:
                parameters = self._read_parameters()
                #**dictionary means to "treat the key-value pairs in the dictionary as additional named arguments to this function call".
                # This allows us to pass the dictionary to the simulation as arguments.
                print (parameters)
                self._simulation = Simulation(**parameters)
                #we resize the canvas
                self._resize_canvas(parameters["height"], parameters["width"])

                self._reset_button.configure(state=tk.NORMAL)

                self._render_grid()
                self._update_statistics()
            #if an error happened
            except (ValueError, TypeError):
                raise ValueError or TypeError ("Parameters invalid.")

        #now the simulation is running
        self._running = True
        #stert button is disabled
        self._start_button.configure(state=tk.DISABLED)
        #while the reset button is now active
        self._reset_button.configure(state=tk.NORMAL)
        #we display that the simulation is now running
        self._satus.configure(text="Sim. Satus: Running")
        self._animate()

    #this method resents the simulation
    def _on_reset(self) -> None:
        """For this method we need to reset everything to its starting state."""
        #we stop the running of the simulation
        self._running = False

        if self._id_animation is not None:
            #after_cancel() - Cancel scheduling of function identified with ID.Identifier returned by after or after_idle must be given as first parameter.
            #by using this we can give the animation id to canal the corresponding delay in animation
            self._root.after_cancel(self._id_animation)
            self._id_animation = None # then we set the ID back to nothing
        #seting the simulation to nothing as in the beginning
        self._simulation = None
        self._canvas.delete("all")#this deletes all that is on the canvas

        # then we make the start boon active
        self._start_button.configure(state=tk.NORMAL)

        #we set the statistics to their starting states
        self._step.configure(text="Step: -")
        self._susceptible.configure(text="Susceptible: -")
        self._infected.configure(text="Infected: -")
        self._recovered.configure(text="Recovered: -")
        self._r0.configure(text="R\u2080: -")
        self._satus.configure(text="Sim. Satus: -")

    def _animate(self) -> None:
        #if the simulation is not running or doesn't exist
        if (not self._running) or ( self._simulation is None):
            return

        #goes through a simulation step and returns a boolean weather the simulation is still running
        is_still_running = self._simulation.simulation_update()

        #the grid is re-rendered and stats are updated
        self._render_grid()
        self._update_statistics()

        if is_still_running:
            #we assign the id of the time delay procedure ti the animation id, that way we can cancel it if we need to
            self._id_animation = self._root.after(TIME_DELAY_MS, self._animate)
        else:#else the simulation is complete
            self._simulation_complete()

    #this method is called when the simulation is complete
    def _simulation_complete(self) -> None:
        #the simulation is no longer running
        self._running = False
        #the start button is disabled and reset button is enabled
        self._start_button.configure(state=tk.DISABLED)
        self._reset_button.configure(state=tk.NORMAL)
        #the simulation outputs that it is complete
        self._satus.configure(text="Sim. Satus: Complete")

    def run(self):
        self._root.mainloop()

def main() -> None:
    application = SimulationGUI()
    application.run()

if __name__ == "__main__":
    main()
