"""Konuşan evcil hayvanlar: her durum için (kedi, köpek) tek replik. Kedi alaycı ve umursamaz, köpek coşkulu.
Sesleri gecmiste-sen/tools/voice_lib.py üretir (iş adı 'paw:<Ses>-N' kedi, 'paw:<Ses>-P' köpek) → voices/<Ses>/lines/."""

LINES = {
    'doorbell': ('Not my problem.', 'INTRUDER! INTRUDER!'),
    'vacuum': ('Absolutely not. Bye.', 'I will defeat you, monster!'),
    'food': ('This again? Ugh.', 'FOOD! Best day ever!'),
    'cup': ('Oops. Did that on purpose.', 'Oops! Was that me?'),
    'bath': ('You will pay for this.', 'Splash time! Wheee!'),
    'box': ('If it fits, I sit.', 'Box? Destroy the box!'),
    'laser': ('I will catch you. Someday.', 'My tail! I almost got it!'),
    'cucumber': ('SNAKE! Run!', 'Crunchy! Yummy!'),
    'ball': ('Get it yourself.', 'Again! Throw it again!'),
    'mirror': ('Who is that handsome stranger?', 'New best friend!'),
    'squeaky': ('One squeak is enough.', 'Squeak! Squeak! SQUEAK!'),
    'bed': ('I prefer the box.', 'Best bed ever! Now it is fluff!'),
    'thunder': ('I live under the table now.', 'Hold me. Please hold me.'),
    'treat': ('I do not do tricks.', 'Sit! Spin! Paw! Treat please!'),
    'cake': ('Make a wish. Achoo!', 'Happy birthday to ME!'),
    'mail': ('Mine now.', 'Paper! Shred the paper!'),
    'sunbeam': ('Pure sunshine. Do not disturb.', 'Too hot! Too hot!'),
    'bubbles': ('Betrayed by a bubble.', 'Bubbles! Catch them all!'),
    'fish': ('This means war.', 'Hello, little friend!'),
    'yarn': ('Help. I am tangled.', 'I redecorated the house!'),
}

# kedi → Zephyr (net, alaycı), köpek → Puck (coşkulu)
CAT_VOICE, DOG_VOICE = 'Zephyr', 'Puck'
