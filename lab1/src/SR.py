import time
import typing as tp
from threading import Thread
import enum

from message_queue import Message, MessageCode, LossyMessageQueue


class WndMsgStatus(enum.Enum):
    WAIT_RECEIVE = enum.auto()
    RECEIVED = enum.auto()
    NEED_REPEAT = enum.auto()
    
class WndNode:
    def __init__(self, number:int):
        self.status = WndMsgStatus.NEED_REPEAT
        self.time = 0
        self.number = number
        pass


class SR_transmisser():
    def __init__(self):
        pass

    @staticmethod
    def SR_sender_process(messages_count : int,
                            window_size : int,
                            lost_timeout_sec : float,
                            sending_queue : LossyMessageQueue, 
                            ACK_reciving_queue : LossyMessageQueue,
                            posted_msgs:tp.List[int] = [],
                            is_ACK_has_losses : bool = False
                            ) -> None:

        window_nodes = [WndNode(i) for i in range(window_size)]
        
        received_cnt = 0
        last_from_left_received = -1 # спец переменная: хранит индекс наибольшего подтвержденного пакета, для которого все предыдущие до него также подтвердились 

        # пока не пришли подтверждения от всех пакетов
        while received_cnt != messages_count - 1:
            
            # если пришел ответ
            if (not ACK_reciving_queue.is_empty()):
                answer = ACK_reciving_queue.pop_message()
                is_lost = (answer.status == MessageCode.LOST) if is_ACK_has_losses == True else False

                # пришел ожидаемый ответ
                if (is_lost == False):
                    received_cnt += 1
                    window_nodes[answer.message_pos].status = WndMsgStatus.RECEIVED

                    # сдвигаем границу окна, с которого будем отправлять и принимать 
                    if answer.info_number == last_from_left_received + 1:
                        last_from_left_received += 1
                        
                        # выставляем границы индексов которые могут быть значениями "last_from_left_received"
                        begin, end = last_from_left_received + 1, last_from_left_received + window_size
                        for i in range(last_from_left_received + 1, last_from_left_received + window_size, 1):
                            # значение выше числа сообщений не может быть
                            if i >= messages_count:
                                break
                            # если после обновления "last_from_left_received" оказалось, что правее него есть следующий пакет, который уже прислал ACK, то выбираем его
                            if window_nodes[i % window_size].status == WndMsgStatus.RECEIVED and window_nodes[i % window_size].number == last_from_left_received + 1:
                                last_from_left_received += 1
                            else:
                                break
                    
                
            # Проверяем статус не приславших ACK пакетов
            curr_time = time.time()
            for window in window_nodes:
                if window.number >= messages_count:
                    continue
                if curr_time - window.time > lost_timeout_sec:
                    window.status = WndMsgStatus.NEED_REPEAT

            # отправляем новые пакеты или переотправляем старые
            for i, window in enumerate(window_nodes):
                if window.number >= messages_count:
                    continue

                if window.status == WndMsgStatus.WAIT_RECEIVE:
                    continue
                
                # переотправляем старые неподтвержденые пакеты
                elif window.status == WndMsgStatus.NEED_REPEAT:
                    window.status = WndMsgStatus.WAIT_RECEIVE
                    window.time = time.time()

                    msg = Message()
                    msg.info_number = window.number
                    msg.message_pos = i
                    sending_queue.push_message(msg)
                    posted_msgs.append(f"{msg.info_number}({msg.message_pos})")

                # если свободный - пробуем отправить новый (если попадает в сдвинутое окно)
                elif window.status == WndMsgStatus.RECEIVED:
                    new_msg_num = window.number + window_size

                    # если превышаем значение макс кол-ва пакетов или новый пакет у нас находится вне окна
                    if not (new_msg_num < messages_count and last_from_left_received < new_msg_num and new_msg_num <= last_from_left_received + window_size): 
                        continue
                    
                    window.status = WndMsgStatus.WAIT_RECEIVE
                    window.time = time.time()
                    window.number = new_msg_num

                    msg = Message()
                    msg.message_pos = i
                    msg.info_number = new_msg_num
                    sending_queue.push_message(msg)
                    posted_msgs.append(f"{msg.info_number}({msg.message_pos})")

        # получили все ACK - отправляем STOP, не взирая на возможную потерю пакета (мы это не учитываем)
        stop_msg = Message()
        stop_msg.info_number = messages_count
        stop_msg.message_pos = messages_count % window_size
        stop_msg.data = "STOP"
        sending_queue.push_message(stop_msg)
        return


    @staticmethod
    def SR_receiver_process(window_size : int,
                            sending_queue : LossyMessageQueue, 
                            ACK_reciving_queue : LossyMessageQueue,
                            received_msgs:tp.List[int] = []
                            ) -> None:

        # Пока не прочли стоп
        while True:
            if not sending_queue.is_empty():
                curr_msg = sending_queue.pop_message()
                
                # если отправили нам спецсимвол конца - то заканчиваем прием
                # PS: оно может затеряться, но тогда для разрешения пробелмы надо заводить таймер отсутствия приходящих сообщений, 
                # а он на подсчет времени передачи влияет 
                if curr_msg.data == "STOP":
                    break

                # если сообщение затеряно - дем дальш
                if curr_msg.status == MessageCode.LOST:
                    continue

                # если все таки нет - отправляем ACK с полученным номером окна
                ans = Message()
                ans.info_number = curr_msg.info_number
                ans.message_pos = curr_msg.message_pos
                ACK_reciving_queue.push_message(ans)
                received_msgs.append(f"{curr_msg.info_number}({curr_msg.message_pos})")
        return 


    @staticmethod
    def make_simulation(messages_count : int,
                        window_size : int,
                        lost_timeout_sec : float,
                        lost_propability : float):

        # init queues and lists
        sending_queue = LossyMessageQueue(lost_propability=lost_propability)
        ACK_queue = LossyMessageQueue(lost_propability=lost_propability)
        posted_msgs, received_msgs = [], []

        # init multithread works
        sender_th = Thread(target=SR_transmisser.SR_sender_process, args=(messages_count, window_size, lost_timeout_sec, sending_queue, ACK_queue, posted_msgs))
        receiver_th = Thread(target=SR_transmisser.SR_receiver_process, args=(window_size, sending_queue, ACK_queue, received_msgs))

        # count time
        timer_start = time.time()
        receiver_th.start()
        sender_th.start()
        
        sender_th.join()
        receiver_th.join()
        timer_end = time.time()

        # return info about simulation
        return received_msgs, posted_msgs, len(received_msgs) / len(posted_msgs), timer_end - timer_start 

