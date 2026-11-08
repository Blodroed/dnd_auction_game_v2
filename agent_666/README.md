# Agent 666 - DoomGuy666

## Gold and points

You only earn points if you get the dice from the bid. See [[#DND dice mechanic]] on how many points you get.

60% back if you do not win the auction

## DND dice mechanic

You bid on dice throws

```txt
Example:
5 + 3d6
5 + 1 + 3 + 1 = 10
```

## Interest in the gold bank

- Interest you get back on money in the bank. Max peak
- Randomly determined, everyone get's the same amount

## Settings and variables

**connected**(bool): if we are connected or not
**connection_info**(dict):

- **host**(string): <http://www.localhost.com>
- **agent_name**(string): Agent name
- **player_id**(string): player id
- **port**(int): port number

**game_sections**(dict):

- **start**(float): percantage of total rounds
- **mid**(float): percantage of total rounds
- **end**(float): percentage of total rounds

**strategies**(dict):

- **start**(string): strategy_mode
- **mid**(float): strategy_mode
- **end**(float): strategy_mode

## Tips

Use try excepts everywhere. And a for loop which reconnects.

## How much information do we have

- You get information on how much money everyone has: attached in the file [[server-output-schema.json]]
- 1000 rounds + break + 1000 rounds
  - 1s per round
- expected 30 players
  - this means 45 active auctions
- We cannot know how much money a player has, but we do know that they are over or under the current bank limit.
- Current implementation says that players are not able to have more gold than the (upper_bank_limit \* interest) + gold income

## Max payout

The max payout is determined by `Max Payout = (Bank_limit * Interest Rate) + Gold Income` each round. Players who are below this bar we know does not have at least bank_limit in their bank account.

## 🧾 Server Output Overview

The server provides a comprehensive snapshot of the game state, including agent statistics, auction details, and economic parameters. Here's what each field represents:

### 🔢 Round Information

- **`round`** _(integer)_:  
   The current round number in the game.

### 🧍 Agent States

- **`states`** _(object)_:  
   A dictionary mapping each agent ID to their current:
  - `gold`: Amount of gold the agent earned this round.
  - `points`: Number of points the agent has earned.

### 🏦 Current Auctions

- **`auctions`** _(object)_:  
   A dictionary of ongoing auctions, where each auction includes:
  - `die`: Type of die used (e.g., 6 for a d6).
  - `num`: Number of dice rolled.
  - `bonus`: Bonus added to the total dice roll.

### ⏮️ Previous Auctions

- **`prev_auctions`** _(object)_:  
   A dictionary of auctions from the previous round, detailing:
  - `winner`: ID of the agent who won the auction.
  - `reward`: Points awarded to the winner.
  - `bids`: Dictionary of bids placed by each agent.

### 💰 Economic Parameters

These arrays define the economic conditions for upcoming rounds:

- **`remainder_gold_income`** _(array of numbers)_:  
   Gold income values for each remaining round.
- **`remainder_bank_limit`** _(array of numbers)_:  
   Bank limit values for each remaining round.
- **`remainder_bank_interest`** _(array of numbers)_:  
   Bank interest rates for each remaining round.

<https://github.com/ooki/dnd_auction_game/tree/main>

# Code review and cracktastics

## 🏛️ AuctionHouse Relevant Properties

### 💰 Economic Parameters

- **Gold Income**: 1000
- **Auctions per Agent**: 1.5
- **Gold Back Fraction**: 0.6

### 🎲 Die Configuration

```python
# Will probably be changed when actual game is running
self.die_sizes  = [2,   3,  4,  6,   8, 10,  12,  20,  20]
self.die_prob   = [8,   8,  9,  8,   6,  6,   5,   2,   1]
self.max_n_die  = [5,   7, 10,  2,   3,  3,   6,   2,   4]
self.max_bonus  = [10,  2, 16,  8,  21,  2,   5,   7,   3]
self.min_bonus  = [-2, -8, -5, -5, -10, -4, -5,  -4,   -4]
```

### 📈 Income and interest

The gold income, bank limit and bank interest per round is set at the start so we can have a future outlook on how the auction game will progress from the first auction round.

#### 💰 Gold income

Params:

- gold_per_round = 1000
- step_size = 150
- max_gold_per_round = 3000

Starts at gold_per_round, then next round goes up or down randomly within step_size. Does not go below 0, and max cap is set to max_gold_per_round. At round 500, gold\[-1\] is getting set to gold_per_round as a reset.

#### 🏦 Bravos bank limit

Params:

- upper_limit_start = 2000
- uppper_limit_end = 10000
- step_size = 150

Starts at upper_limit_start, then next round goes up or down randomly within step_size. Minimum cap at 0, and max cap is set to upper_limit_end. At round 300, upper_limits\[-1\] is getting set to upper_limit_start as a reset.

#### 📈 Interest rate

Params:

- start_rate = 1.03
- min_rate = 0.85
- max_rate = 1.15
- step_size = 0.02

Starts at start_rate, then next round goes up or down randomly within step_size. Minimum cap at min_rate, and max cap is set max_rate. At round 250, rates\[-1\] is getting set to upper_limit_start as a reset.

## Dice pool value

There are going to be at least 30 auctions going on at the time that means we can estimate from the winning bids what each dice is worth.

### Example

Data:
![[Auction_bids.loom]]
Data schema:

- round_n: integer
- auction_id: text(ax)
- die_values: array\[integer\]
  - (die, num, bonus)
- winner: string
  - Who won the auction, found in round\[+1]
- winning bid: integer
  - the winning bid for auction, found in round\[+1]
- bids: array\[integer]
  - all bids on that auction
- reward: integer
  - The rolled reward given to the winning player, found in round\[+1]

# Strategies

Divide the 1000 round game into 3 phases early, mid, end. People are more likely to be conservative in the start and risker towards the end because of the interest. The middle of the game is where general accumulation can happen.

Terms:

- **mean_winner_bid**: mean value of the die on bids
- [[#Max payout]]: the max payout a player can get on a single round

## Start methods

### High risk start, then educated guesses

In the start we can take more risks at most wealth is not accumulated yet and many might try to fill their bank to get over the bank upper limit for max gold gains.

### Slow start

Wait out a couple of rounds to build up your wealth, then use the accumulated knowledge for taking educated guesses.

### Exploratory start

Place small bids on various auctions to gather information about other agents' strategies.

## Bidding strategies

### High Risk High Reward

Betting on high risk dice rolls with high potential payoffs. Put money into only bids with dice above thresholds (eg. d12, d20) to maximize potential points.

### VULTURE MODE {exploit deadspace}

After a few runs the we will get a landscape of die that people either are not bidding on, or bidding very low on. We can exploit this deadspace to bid and win the most amount of dice.

For the dashboard we might want to display green zones for good strike zones.

Table format:
Column_name: die formats (d2,d3,d4,d6,d8,...,d20)
Row_name: num die (1, 2, ..., 10)

### Anonymous gamblers exploit

Exploit that agressive players has less money this round because they do not exceed the [[#Max payout]] this round. We only do this tactic if a certain threshold of players does not have above bank_limit.

### Interest based

Look ahead on the timeline and find out where we are going to lose money, start bidding there

### Big splash mode

Find out where we could save up a lot of money, and then bid over the **mean_winner_bid** rate on high score auctions in a low interest period.

## Bid mode

The bid modes are how the bot distributes bidding after the bidding strategy has selected their best selection.

### All or nothing

Bid only on 1-x(user input) select few the bot decides. Sets a max amount of biddings so that we can claim at least some.

### Higher lower earnings

Make sure the best bid is 50% of what we want to bid this round, and distribute the rest according to the mean score of the dice roll.

### Even Steven

Bet evenly on the selected bets.

### Mean green killing machine

Determine bids amount based on the mean bid value and the standard deviation, being always over the standard deviation + mean.

## Extra notes

**Analyze Die Config:** Identify the die/num/bonus combination players won and calculate the average Expected Value (EV). If they overpaid, you know their valuation is higher than yours.

# Security vulnerabilites

the player_id is set by the player and truncated to 128 characters. Since there are examples most persons would probably use the preset "id_of_human_player". We could scan through the player names and then try to connect with this first to bid on stuff
