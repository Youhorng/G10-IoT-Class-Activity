# ── state.py — shared system state ───────────────────────────
class ParkingState:
    def __init__(self):
        self.slots=[False]*5; self.gate_open=False
        self.light_on=False; self.temperature=0.0; self.humidity=0.0
        self.car_at_entry=False; self.car_at_exit=False
        self._last_event = None
        self._last_slots = [False] * 5

    @property
    def total(self):      return len(self.slots)
    @property
    def available(self):  return self.slots.count(False)
    @property
    def is_full(self):    return self.available==0
    @property
    def is_occupied(self):return self.slots.count(True)>0

    def slot_label(self,i): return "OCCUPIED" if self.slots[i] else "FREE"

    def summary(self):
        g="OPEN" if self.gate_open else "CLOSED"
        l="ON"   if self.light_on  else "OFF"
        s="FULL" if self.is_full   else str(self.available)+" free"
        return ("=== Smart Parking ===\n"
                "Slots : "+s+" ("+str(self.available)+"/"+str(self.total)+")\n"
                "Gate  : "+g+"\nLights: "+l+"\n"
                "Temp  : "+str(self.temperature)+" C\n"
                "Humid : "+str(self.humidity)+" %")

    def lcd_lines(self):
        # Line 1: "1E 2X 3E 4E 5E" — E=empty F=occupied
        line1 = " ".join(str(i+1)+("F" if self.slots[i] else "E") for i in range(self.total))

        # Line 2: gate status + event
        g = "O" if self.gate_open else "C"
        if self.is_full:
            line2 = "G:" + g + " Parking Full"
        elif self.car_at_entry:
            line2 = "G:" + g + " Car In"
        elif self.car_at_exit:
            line2 = "G:" + g + " Car Out"
        else:
            line2 = "G:" + g + " Free Slot: " + str(self.available)  

        return line1[:16], line2[:16]
    #def get_event(self):
        #"""Returns event string when something changes, None if nothing new."""
        #if self.is_full:
            #return "Parking FULL\nAll 5 slots occupied"
        #elif self.car_at_entry and self.gate_open:
            #return "Car entering\nFree slots: " + str(self.available)
        #elif self.car_at_exit and self.gate_open:
            #return "Car exiting\nFree slots: " + str(self.available)
        #return None
    def get_event(self):
        g = "Open" if self.gate_open else "Close"
        
        if self.is_full:
            return "Gate:" + g + " Parking Full"
        
        elif self.car_at_entry and self.gate_open:
            # Find which slot just got occupied
            occupied = [i+1 for i in range(self.total) if self.slots[i]]
            slot_info = "Slot " + str(occupied[-1]) + " occupied" if occupied else ""
            return "Gate:" + g + " Car Entered\n" + slot_info
        
        elif self.car_at_exit and self.gate_open:
            # Find which slots are still occupied
            free = [i+1 for i in range(self.total) if not self.slots[i]]
            slot_info = "Slot " + str(free[0]) + " now free" if free else ""
            return "Gate:" + g + " Car Exited\n" + slot_info
        
        else:
            return None

state=ParkingState()

