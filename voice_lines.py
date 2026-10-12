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

# 2026-10-12: her duruma 2 replik daha (kedi, köpek) → <durum>_<N|P><2|3>.wav
MORE = {
    'doorbell': (('Someone else will get it.', 'I am sleeping. Go away.'), ('Who is it?! WHO IS IT?!', 'Friend? Enemy? FRIEND!')),
    'vacuum': (('The beast is back. I am out.', 'Nope. Nope. Nope.'), ('Get back, you noisy monster!', 'I protect this house!')),
    'food': (('Where is the salmon?', 'I will think about it.'), ('Is it dinner? It is dinner!', 'Gone! More, please!')),
    'cup': (('Gravity test. Success.', 'It was in my way.'), ('My tail did it!', 'Sorry! Still love me?')),
    'bath': (('Water is my enemy.', 'I will remember this.'), ('Bubbles! I love bubbles!', 'Again! Bath again!')),
    'box': (('My new castle.', 'Best gift ever. The box.'), ('Box attack!', 'Cardboard confetti!')),
    'laser': (('Red dot, you are mine!', 'I meant to hit the wall.'), ('Round and round!', 'I see my tail! Get it!')),
    'cucumber': (('Green monster! Abort!', 'Who put that there?!'), ('Green snack!', 'Crunch time!')),
    'ball': (('You throw it, you fetch it.', 'I am busy. Napping.'), ('Ball! Ball! BALL!', 'Throw it one more time!')),
    'mirror': (('Another cat? In MY house?', 'Fight me, stranger.'), ('Hi! Want to play?', 'You look great, buddy!')),
    'squeaky': (('That noise is offensive.', 'Squeak. Boring.'), ('Best toy ever!', 'Squeaky squeaky squeak!')),
    'bed': (('Beds are overrated.', 'Box is my bed now.'), ('Fluffy! Shake it!', 'I made it comfier!')),
    'thunder': (('The sky is angry. I hide.', 'Wake me when it stops.'), ('Scary sky noise!', 'Can I sleep with you?')),
    'treat': (('Give it. Now.', 'Tricks are beneath me.'), ('Look! I can spin!', 'Good boy wants a treat!')),
    'cake': (('Too much fire. Achoo.', 'Candles are drama.'), ('Cake! Cake! Cake!', 'Face first! Yum!')),
    'mail': (('Warm paper. Perfect bed.', 'This is my desk now.'), ('Mail monster defeated!', 'I read it! I ate it!')),
    'sunbeam': (('Sun nap. Do not disturb.', 'I am melting. Happily.'), ('Hot! Need shade!', 'Panting! Pant pant!')),
    'bubbles': (('I trusted you, bubble.', 'Achoo. Rude.'), ('Got one! Got another!', 'Pop! Pop! Pop!')),
    'fish': (('Swim closer, little snack.', 'I am soaked. Revenge.'), ('Hello, fishy friend!', 'Can we play?')),
    'yarn': (('This is fine. I am fine.', 'Untangle me. Now.'), ('Long string! Run!', 'Look what I made!')),
}
