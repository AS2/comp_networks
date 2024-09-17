import time
import typing as tp
from threading import Thread
import enum

from message_queue import Message, MessageCode, LossyMessageQueue

class SR_transmisser():
    def __init__(self):
        pass

    class WndMsgStatus(enum.Enum):
        BUSY = enum.auto()
        NEED_REPEAT = enum.auto()
        CAN_BE_USED = enum.auto()

    class WndNode:
        def __init__(self, number):
            self.status = WndMsgStatus.NEED_REPEAT
            self.time = 0
            self.number = number
            pass

    @staticmethod
    def GBN_sender_process(messages_count : int,
                            window_size : int,
                            lost_timeout_sec : float,
                            sending_queue : LossyMessageQueue, 
                            ACK_reciving_queue : LossyMessageQueue,
                            posted_msgs:tp.List[int] = [],
                            is_ACK_has_losses : bool = False
                            ) -> None:

        current_message = 0
        last_ACK_received = -1
        last_received_time = time.time()

        # пока не пришли подтверждения от всех пакетов
        while last_ACK_received != messages_count - 1: # пока не получили уведомление о последнем пакете
            expected_ACK = (last_ACK_received + 1) % window_size
            
            # пришел ответ
            if (not ACK_reciving_queue.is_empty()):
                answer = ACK_reciving_queue.pop_message()
                is_lost = (answer.status == MessageCode.LOST) if is_ACK_has_losses == True else False

                #print(f"Received answer: {answer.message_pos}, expected ACK: {expected_ACK}")
                # пришел ожидаемый ответ
                if (is_lost == False and answer.message_pos == expected_ACK):
                    last_ACK_received += 1
                    last_received_time = time.time()
                # пришел неожиданный ответ
                else:
                    current_message = last_ACK_received + 1
                    last_received_time = time.time()
                
            # не пришел ответ...
            else:
                # ...долгое время
                if time.time() - last_received_time > lost_timeout_sec:
                    current_message = last_ACK_received + 1
                    last_received_time = time.time()

            # отправляем пакеты которые еще попадают в окно
            if (current_message < messages_count) and (current_message < last_ACK_received + window_size):
                #print(f"sending:{current_message}, expecting:{expected_ACK}")
                new_msg = Message()
                new_msg.info_number = current_message
                new_msg.message_pos = current_message % window_size
                sending_queue.push_message(new_msg)
                posted_msgs.append(new_msg.info_number)
                current_message += 1

        # получили все ACK - отправляем STOP, не взирая на возможную потерю пакета (мы это не учитываем)
        stop_msg = Message()
        stop_msg.info_number = current_message
        stop_msg.message_pos = current_message % window_size
        stop_msg.data = "STOP"
        sending_queue.push_message(stop_msg)
        return


    @staticmethod
    def GBN_receiver_process(window_size : int,
                            sending_queue : LossyMessageQueue, 
                            ACK_reciving_queue : LossyMessageQueue,
                            received_msgs:tp.List[int] = []
                            ) -> None:

        expected_number = 0
    
        # Пока не прочли стоп
        while True:
            if not sending_queue.is_empty():
                #print(f"expecting:{expected_number}")
                curr_msg = sending_queue.pop_message()
                
                # если отправили нам спецсимвол конца - то заканчиваем прием
                # PS: оно может затеряться, но тогда для разрешения пробелмы надо заводить таймер отсутствия приходящих сообщений, 
                # а он на подсчет времени передачи влияет 
                if curr_msg.data == "STOP":
                    break

                # если сообщение затеряно - дем дальш
                if curr_msg.status == MessageCode.LOST:
                    continue

                # если все таки нет, и оно еще и то, которое ожидаем - отправляем ACK с нужным номером окна
                if curr_msg.message_pos == expected_number:
                    ans = Message()
                    ans.message_pos = curr_msg.message_pos
                    ACK_reciving_queue.push_message(ans)

                    received_msgs.append(f"{curr_msg.info_number}({curr_msg.message_pos})")
                    expected_number = (expected_number + 1) % window_size
                else:
                    continue
        
        return 

    # @staticmethod
    # def __create_GBN_sending(sending_queue : LossyMessageQueue, 
    #                         ACK_reciving_queue : LossyMessageQueue,
    #                         posted_msgs:tp.List[int]):

    #     def sim_GBN_sender(messages_count : int,
    #                         window_size : int,
    #                         lost_timeout_sec : float):
    #         return GBN_transmisser.GBN_sender_process(messages_count, window_size, lost_timeout_sec, sending_queue, ACK_reciving_queue, posted_msgs)
    #     return sim_GBN_sender

    # @staticmethod
    # def __create_GBN_receiving(sending_queue : LossyMessageQueue, 
    #                         ACK_reciving_queue : LossyMessageQueue,
    #                         received_msgs:tp.List[int]):

    #     def sim_GBN_reciever(window_size:int):
    #         return GBN_transmisser.GBN_receiver_process(window_size, sending_queue, ACK_reciving_queue, received_msgs)
    #     return sim_GBN_reciever


    @staticmethod
    def make_simulation(messages_count : int,
                        window_size : int,
                        lost_timeout_sec : float,
                        lost_propability : float):

        # init queues and lists
        sending_queue = LossyMessageQueue(lost_propability=lost_propability)
        ACK_queue = LossyMessageQueue(lost_propability=lost_propability)
        posted_msgs, received_msgs = [], []

        # ACK_queue.push_message(Message(0, 0))
        # ACK_queue.push_message(Message(1, 1))
        # ACK_queue.push_message(Message(2, 2))
        # ACK_queue.push_message(Message(3, 0))
        # ACK_queue.push_message(Message(4, 1))

        #sending_queue.push_message(Message(1, 0))
        #sending_queue.push_message(Message(1, 1))
        #sending_queue.push_message(Message(1, 2))

        # init multithread works
        sender_th = Thread(target=GBN_transmisser.GBN_sender_process, args=(messages_count, window_size, lost_timeout_sec, sending_queue, ACK_queue, posted_msgs))
        receiver_th = Thread(target=GBN_transmisser.GBN_receiver_process, args=(window_size, sending_queue, ACK_queue, received_msgs))

        # count time
        timer_start = time.time()
        receiver_th.start()
        sender_th.start()
        #GBN_transmisser.GBN_sender_process(messages_count, window_size, lost_timeout_sec, sending_queue, ACK_queue, posted_msgs)
        #GBN_transmisser.GBN_receiver_process(window_size, sending_queue, ACK_queue, received_msgs)
        
        sender_th.join()
        receiver_th.join()
        timer_end = time.time()

        # return info about simulation
        return received_msgs, posted_msgs, len(received_msgs) / len(posted_msgs), timer_end - timer_start 

