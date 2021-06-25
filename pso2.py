#this bot has nothing to do with the pixiv stuff
#just some other bot ideas I had for phantasy star online 2

class Quest:
    def __init__(self, name, diff, clear, char, quest_id):
        self.name = name
        self.diff = diff
        self.clear = clear
        self.char = char
        self.quest_id = quest_id

    @staticmethod
    def compare_exact(quest1, quest2):
        if quest1.name == quest2.name and quest1.diff == quest2.diff and quest1.clear == quest2.clear and quest1.char != quest2.char:
            return True
        else:
            return False

    @staticmethod
    def compare_loose(quest1, quest2):
        if quest1.name == quest2.name and quest1.char != quest2.char:
            return True
        else:
            return False

class Quest_list:
    def __init__(self):
        self.quests = []
        
    def add(self, quest):
        #check list size
        if len(self.quests) == 60:
            return "client orders limit reached"
        #check for dupes
        self.quests.append(quest)

    @staticmethod
    def sort_list(quest_list):
        quest_list.sort(key=lambda quest: quest.name)
        
    def remove_name(self, quest):
        self.quests.remove(quest)
        #might need to code this

    def remove_idx(self, idx):
        #check for out of range
        quest = self.quests.pop(idx)
        return quest
    
    def get_id(self, idx):
        return self.quests[idx].quest_id

    @staticmethod
    def compare_lists_loose(list1, list2):
        #find a good algorithm for this
        same_quests = ''
        #concat into one list
        #sort the list
        list3 = Quest_list()
        list3.quests = list1.quests + list2.quests
        Quest_list.sort_list(list3.quests)
        #loop and compare
        recent = ''
        for i in range(len(list3.quests) - 1):
            if Quest.compare_loose(list3.quests[i], list3.quests[i + 1]):
                if list3.quests[i + 1].name != recent:
                    same_quests = same_quests + list3.quests[i].name +'\n'
                #prevents dupe names
                recent = list3.quests[i + 1].name

        print("Quest_list.compare_lists_loose:")
        print(type(same_quests))
        print(same_quests)

        return same_quests#return a string

    def listToString(self, character_name):
        returnThis = 'client orders for ' + character_name + ' :\n'
        for i in range(len(self.quests)):
            returnThis += str(i + 1) + ': ' + self.quests[i].name + ' ' + self.quests[i].diff + ' rank: ' + self.quests[i].clear + '\n'
        return returnThis
    
class Character:
    def __init__(self, name, user_name, user_id):
        self.user_name = user_name
        self.user_id = user_id
        self.name = name
        self.quest_list = Quest_list()

    @staticmethod
    def compare_char_loose(char1, char2):#takes in character
        print("compare ids:")
        print(char1.user_id)
        print(char2.user_id)
        if char1.user_id == char2.user_id:#characters belong to same user
            print("not returning string")
            return
        matches = Quest_list.compare_lists_loose(char1.quest_list, char2.quest_list)
        #matches is a string
        print("Character.compare_char_loose:")
        print(type(matches))
        print(matches)
        return matches


class Daily_list:
    def __init__(self, quest_list):
        self.quest_list = quest_list

def main():
    pass

main()