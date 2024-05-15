import random
import numpy as np
import csv
import tensorflow as tf

class Ship:
    def __init__(self, size):
        self.row = random.randrange(0, 10 - size + 1)
        self.col = random.randrange(0, 10 - size + 1)
        self.size = size
        self.orientation = random.choice(["h", "v"])
        self.indexes = self.compute_indexes()

    def compute_indexes(self):
        start_index = self.row * 10 + self.col
        if self.orientation == "h":
            return [start_index + i for i in range(self.size)]
        elif self.orientation == "v":
            return [start_index + i * 10 for i in range(self.size)]

class Player:
    def __init__(self):
        self.ships = []
        self.search = ["U" for _ in range(100)]  # U = unknown
        self.place_ships(sizes=[5, 4, 3, 3, 2])
        list_of_lists = [ship.indexes for ship in self.ships]
        self.indexes = [index for sublist in list_of_lists for index in sublist]

    def place_ships(self, sizes):
        for size in sizes:
            placed = False
            while not placed:
                ship = Ship(size)
                possible = True
                for i in ship.indexes:
                    if i >= 100:
                        possible = False
                        break
                    new_row = i // 10
                    new_col = i % 10
                    if new_row != ship.row and new_col != ship.col:
                        possible = False
                        break
                    for other_ship in self.ships:
                        if i in other_ship.indexes:
                            possible = False
                            break
                if possible:
                    self.ships.append(ship)
                    placed = True

    def show_ships(self):
        indexes = ["-" if i not in self.indexes else "X" for i in range(100)]
        for row in range(10):
            print(" ".join(indexes[(row - 1) * 10 : row * 10]))

class Game:
    def __init__(self, human1, human2):
        self.human1 = human1
        self.human2 = human2
        self.player1 = Player()
        self.player2 = Player()
        self.play1_turn = True
        self.computer_turn = True if not human1 else False
        self.over = False
        self.result = None
        self.n_shot = 0

    def make_move(self, i):
        player = self.player1 if self.play1_turn else self.player2
        opponent = self.player2 if self.play1_turn else self.player1
        hit = False
        if i in opponent.indexes:
            player.search[i] = "H"
            hit = True
            for ship in opponent.ships:
                sunk = True
                for idx in ship.indexes:
                    if player.search[idx] == "U":
                        sunk = False
                        break
                if sunk:
                    for idx in ship.indexes:
                        player.search[idx] = "S"
        else:
            player.search[i] = "M"
        game_over = True
        for idx in opponent.indexes:
            if player.search[idx] == "U":
                game_over = False
        self.over = game_over
        self.result = 1 if self.play1_turn else 2
        if not hit:
            self.play1_turn = not self.play1_turn
            if (self.human1 and not self.human2) or (not self.human1 and self.human2):
                self.computer_turn = not self.computer_turn
        self.n_shot += 1

    def random_ai(self):
        search = self.player1.search if self.play1_turn else self.player2.search
        unknown = [i for i, square in enumerate(search) if square == "U"]
        if len(unknown) > 0:
            random_index = random.choice(unknown)
            self.make_move(random_index)

    def basic_ai(self):
        search = self.player1.search if self.play1_turn else self.player2.search
        unknown = [i for i, square in enumerate(search) if square == "U"]
        hits = [i for i, square in enumerate(search) if square == "H"]
        unknown_with_neighbors_hits1 = []
        unknown_with_neighbors_hits2 = []
        for u in unknown:
            if u + 1 in hits or u - 1 in hits or u + 10 in hits or u - 10 in hits:
                unknown_with_neighbors_hits1.append(u)
            if u + 2 in hits or u - 2 in hits or u + 20 in hits or u - 20 in hits:
                unknown_with_neighbors_hits2.append(u)
        for u in unknown:
            if u in unknown_with_neighbors_hits1 and u in unknown_with_neighbors_hits2:
                self.make_move(u)
                return
        if len(unknown_with_neighbors_hits1) > 0:
            self.make_move(random.choice(unknown_with_neighbors_hits1))
            return
        checker_board = []
        for u in unknown:
            row = u // 10
            col = u % 10
            if (row + col) % 2 == 0:
                checker_board.append(u)
        if len(checker_board) > 0:
            self.make_move(random.choice(checker_board))
            return
        self.random_ai()

# DQN Parameters
GAMMA = 0.95
MEMORY_CAPACITY = 1000
BATCH_SIZE = 32
memory = []

def remember(state, action, reward, next_state):
    memory.append((state, action, reward, next_state))
    if len(memory) > MEMORY_CAPACITY:
        del memory[0]

def train_dqn(agent, memory, batch_size=BATCH_SIZE):
    if len(memory) < batch_size:
        return
    minibatch = random.sample(memory, batch_size)
    for state, action, reward, next_state in minibatch:
        target = reward
        if next_state is not None:
            target = (reward + GAMMA * np.amax(agent.model.predict(next_state)[0]))
        target_f = agent.model.predict(state)
        target_f[0][action] = target
        agent.model.fit(state, target_f, epochs=1, verbose=0)

class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.model = self.build_model()

    def build_model(self):
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(24, activation='relu', input_shape=(self.state_size,)),
            tf.keras.layers.Dense(24, activation='relu'),
            tf.keras.layers.Dense(self.action_size, activation='linear')
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def act(self, state):
        return np.argmax(self.model.predict(state)[0])

def train_agent_from_csv(filename):
    with open(filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            state = np.array([[int(row['Row']), int(row['Column'])]])  # Thêm một chiều cho kích thước (None, 2)
            action = random.randint(0, 1)
            reward = 0
            next_state = None
            remember(state, action, reward, next_state)

train_agent_from_csv('playermoves.csv')
agent = DQNAgent(state_size=2, action_size=2)
train_dqn(agent, memory)

def suggest_next_move_combined(agent, player, hit_probabilities):
    max_probability = np.max(hit_probabilities)
    if max_probability > 0.5:  # Luôn hiển thị gợi ý
        row_prob, col_prob = np.where(hit_probabilities == max_probability)
        row_prob, col_prob = row_prob[0], col_prob[0]
        state = np.array([[row_prob, col_prob]])
        action_dqn = agent.act(state)  # Dự đoán hành động tiếp theo từ mô hình DQN
        row_dqn, col_dqn = action_dqn // 10, action_dqn % 10

        # Kết hợp gợi ý từ DQN và từ dữ liệu hit_probabilities
        row_combined, col_combined = row_dqn, col_dqn
        if player.search[row_dqn * 10 + col_dqn] == "U":
            row_combined, col_combined = row_prob, col_prob

        return row_combined, col_combined
    else:
        # Nếu không có xác suất trúng tàu, chọn ngẫu nhiên một ô chưa bắn
        unknown = [i for i, square in enumerate(player.search) if square == "U"]
        if len(unknown) > 0:
            random_index = random.choice(unknown)
            row_random, col_random = random_index // 10, random_index % 10
            return row_random, col_random
        else:
            return None, None
