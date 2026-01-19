export const OCS = [
    {
        key: "break_the_bank",
        name: "Break The Bank (Level 8)",
        roles: [
            { id: "robber", name: "Robber", color: "#eab308" }, // yellow-500
            { id: "m1", name: "Muscle 1", color: "#60a5fa" },   // blue-400
            { id: "m2", name: "Muscle 2", color: "#c084fc" },   // purple-400
            { id: "m3", name: "Muscle 3", color: "#2dd4bf" },   // teal-400
            { id: "t1", name: "Thief 1", color: "#fb923c" },    // orange-400
            { id: "t2", name: "Thief 2", color: "#ef4444" }     // red-500
        ],
        nodes: {
            "start": { x: 60, y: 150, type: "start", next: "n1", label: "START" },

            // Col 1 (x=200)
            "n1": { x: 200, y: 150, type: "step", roles: ["robber", "m1"], label: "Robber\nMuscle 1", color: "#f1c40f", pass: "n2", fail: "n1_sub" },
            "n1_sub": { x: 200, y: 280, type: "step", roles: ["m2"], label: "Muscle 2", color: "#9b59b6", pass: "n2", fail: "n1_sub2" },
            "n1_sub2": { x: 200, y: 410, type: "step", roles: ["m3"], label: "Muscle 3", color: "#16a085", pass: "n2", fail: "be1" },
            "be1": { x: 200, y: 540, type: "end", label: "Bad End #1", style: "bad" },

            // Col 2 (x=360)
            "n2": { x: 360, y: 150, type: "step", roles: ["m2"], label: "Muscle 2", color: "#9b59b6", pass: "n3", fail: "n2_sub" },
            "n2_sub": { x: 360, y: 280, type: "step", roles: ["m2", "t1"], label: "Muscle 2\nThief 1", color: "#e67e22", pass: "n3", fail: "n2_sub2" },
            "n2_sub2": { x: 360, y: 410, type: "step", roles: ["t2"], label: "Thief 2", color: "#e74c3c", pass: "sub_m3", fail: "be2" },
            "be2": { x: 360, y: 540, type: "end", label: "Bad End #2", style: "bad" },

            // Branch (GE5) - Offset
            "sub_m3": { x: 480, y: 480, type: "step", roles: ["m3"], label: "Muscle 3", color: "#16a085", pass: "ge5", fail: "sub_m1" },
            "sub_m1": { x: 480, y: 580, type: "step", roles: ["m1"], label: "Muscle 1", color: "#3498db", pass: "ge5", fail: "be3" },
            "ge5": { x: 600, y: 480, type: "end", label: "Good End #5", style: "good", reward: { money: 216237500, respect: 270 } },
            "be3": { x: 600, y: 580, type: "end", label: "Bad End #3", style: "bad" },

            // Col 3 (x=520)
            "n3": { x: 520, y: 150, type: "step", roles: ["m3"], label: "Muscle 3", color: "#16a085", pass: "n4", fail: "n3_sub" },
            "n3_sub": { x: 520, y: 280, type: "step", roles: ["t2"], label: "Thief 2", color: "#e74c3c", pass: "n4", fail: "n4_sub" },

            // Col 4 (x=680)
            "n4": { x: 680, y: 150, type: "step", roles: ["t2"], label: "Thief 2", color: "#e74c3c", pass: "n5", fail: "n4_sub" },
            "n4_sub": { x: 680, y: 350, type: "step", roles: ["robber", "t2"], label: "Robber\nThief 2", color: "#f1c40f", pass: "n5", fail: "be4" },
            "be4": { x: 680, y: 480, type: "end", label: "Bad End #4", style: "bad" },

            // Col 5 (x=840)
            "n5": { x: 840, y: 150, type: "step", roles: ["m3"], label: "Muscle 3", color: "#16a085", pass: "n6", fail: "n5_sub" },
            "n5_sub": { x: 840, y: 280, type: "step", roles: ["m1", "m3"], label: "Muscle 1\nMuscle 3", color: "#3498db", pass: "n6", fail: "be5" },
            "be5": { x: 840, y: 410, type: "end", label: "Bad End #5", style: "bad" },

            // Col 6 (x=1000)
            "n6": { x: 1000, y: 150, type: "step", roles: ["robber", "m1"], label: "Robber\nMuscle 1", color: "#f1c40f", pass: "n7", fail: "n6_sub" },
            // n6_sub accumulates fail from n6 and n7. Position it carefully.
            "n6_sub": { x: 1080, y: 280, type: "step", roles: ["robber"], label: "Robber", color: "#f1c40f", pass: "ge3", fail: "ge4" },

            "n7": { x: 1160, y: 150, type: "step", roles: ["m1"], label: "Muscle 1", color: "#3498db", pass: "n8", fail: "n6_sub" },

            "n8": { x: 1320, y: 150, type: "step", roles: ["robber", "t1"], label: "Robber\nThief 1", color: "#f1c40f", pass: "ge1", fail: "ge2" },

            // Finals
            "ge1": { x: 1480, y: 150, type: "end", label: "Good End #1", style: "good", reward: { money: 376145789, respect: 454 } },
            "ge2": { x: 1320, y: 280, type: "end", label: "Good End #2", style: "good", reward: { money: 333014646, respect: 408 } },
            "ge3": { x: 1180, y: 380, type: "end", label: "Good End #3", style: "good", reward: { money: 295727415, respect: 359 } },
            "ge4": { x: 1000, y: 380, type: "end", label: "Good End #4", style: "good", reward: { money: 256606071, respect: 312 } }
        },
        order: [
            "start",
            "n1", "n1_sub", "n1_sub2", "be1",
            "n2", "n2_sub", "n2_sub2", "be2",
            "sub_m3", "sub_m1", "ge5", "be3",
            "n3", "n3_sub",
            "n4", "n4_sub", "be4",
            "n5", "n5_sub", "be5",
            "n6", "n7", "n6_sub", "ge3", "ge4",
            "n8", "ge1", "ge2"
        ]
    },
    {
        key: "blast_from_the_past",
        name: "Blast From The Past (Level 7)",
        roles: [
            { id: "muscle", name: "Muscle", color: "#2dd4bf" },   // teal-400
            { id: "hacker", name: "Hacker", color: "#60a5fa" },   // blue-400
            { id: "pick1", name: "Picklock 1", color: "#eab308" }, // yellow-500
            { id: "pick2", name: "Picklock 2", color: "#c084fc" }, // purple-400
            { id: "engineer", name: "Engineer", color: "#fb923c" }, // orange-400
            { id: "bomber", name: "Bomber", color: "#ef4444" }     // red-500
        ],
        nodes: {
            "start": { x: 60, y: 150, type: "start", next: "c1", label: "START" },

            // Col 1: Muscle
            "c1": { x: 220, y: 150, type: "step", roles: ["muscle"], label: "Muscle", color: "#2dd4bf", pass: "c2", fail: "c1_s1" },
            "c1_s1": { x: 220, y: 280, type: "step", roles: ["pick1", "pick2"], label: "Picklock 1\nPicklock 2", color: "#eab308", pass: "c2", fail: "c1_s2" },
            "c1_s2": { x: 220, y: 410, type: "step", roles: ["hacker"], label: "Hacker", color: "#60a5fa", pass: "c2", fail: "be1" },
            "be1": { x: 220, y: 540, type: "end", label: "Bad End #1\nNo Reward", style: "bad" },

            // Col 2: Hacker
            "c2": { x: 380, y: 150, type: "step", roles: ["hacker"], label: "Hacker", color: "#60a5fa", pass: "c3", fail: "c2_s1" },
            "c2_s1": { x: 380, y: 300, type: "step", roles: ["pick1"], label: "Picklock 1", color: "#eab308", pass: "c3", fail: "c2_s2" },
            "c2_s2": { x: 380, y: 430, type: "step", roles: ["pick1"], label: "Picklock 1", color: "#eab308", pass: "c3", fail: "be2" },
            "be2": { x: 380, y: 540, type: "end", label: "Bad End #2\nMinor", style: "bad" },

            // Col 3: Muscle
            "c3": { x: 540, y: 150, type: "step", roles: ["muscle"], label: "Muscle", color: "#2dd4bf", pass: "c4", fail: "c3_s1" },
            "c3_s1": { x: 540, y: 300, type: "step", roles: ["muscle"], label: "Muscle", color: "#2dd4bf", pass: "c4", fail: "be3" },
            "be3": { x: 540, y: 450, type: "end", label: "Bad End #3", style: "bad" },

            // Col 4: Engineer
            "c4": { x: 700, y: 150, type: "step", roles: ["engineer"], label: "Engineer", color: "#fb923c", pass: "c5", fail: "c4_s1" },
            "c4_s1": { x: 700, y: 300, type: "step", roles: ["muscle", "engineer"], label: "Muscle\nEngineer", color: "#2dd4bf", pass: "c5", fail: "be4" },
            "be4": { x: 700, y: 450, type: "end", label: "Bad End #4", style: "bad" },

            // Col 5: Bomber
            "c5": { x: 860, y: 150, type: "step", roles: ["bomber"], label: "Bomber", color: "#ef4444", pass: "c6", fail: "c5_s1" },
            "c5_s1": { x: 860, y: 300, type: "step", roles: ["engineer", "bomber"], label: "Engineer\nBomber", color: "#fb923c", pass: "c6_s2", fail: "be5" },
            "be5": { x: 860, y: 450, type: "end", label: "Bad End #5", style: "bad" },

            // Col 6: Pick2 -> Lower Branch Merge
            "c6": { x: 1020, y: 150, type: "step", roles: ["pick2"], label: "Picklock 2", color: "#c084fc", pass: "c7", fail: "c6_s1" },
            "c6_s1": { x: 1020, y: 280, type: "step", roles: ["engineer", "pick2"], label: "Engineer\nPicklock 2", color: "#fb923c", pass: "c7", fail: "c6_s2" },
            "c6_s2": { x: 1020, y: 410, type: "step", roles: ["pick2"], label: "Picklock 2", color: "#c084fc", pass: "low_1", fail: "low_1" },

            // Col 7: Pick1 -> Lower Branch Merge
            "c7": { x: 1180, y: 150, type: "step", roles: ["pick1"], label: "Picklock 1", color: "#eab308", pass: "c8", fail: "c7_s1" },
            "c7_s1": { x: 1180, y: 300, type: "step", roles: ["pick2"], label: "Picklock 2", color: "#c084fc", pass: "c8", fail: "low_1" },

            // Lower Branch (Merge Point)
            "low_1": { x: 1260, y: 560, type: "step", roles: ["pick1"], label: "Picklock 1", color: "#eab308", pass: "low_2", fail: "low_2" },
            "low_2": { x: 1400, y: 650, type: "step", roles: ["hacker"], label: "Hacker", color: "#60a5fa", pass: "ge3", fail: "ge4" },
            "ge3": { x: 1550, y: 580, type: "end", label: "Good End #3", style: "good", reward: { money: 118217940, respect: 281 } },
            "ge4": { x: 1550, y: 720, type: "end", label: "Good End #4", style: "good", reward: { money: 99931212, respect: 248 } },

            // Col 8: Hacker (Main End)
            "c8": { x: 1340, y: 150, type: "step", roles: ["hacker"], label: "Hacker", color: "#60a5fa", pass: "ge1", fail: "ge2" },
            "ge1": { x: 1550, y: 150, type: "end", label: "Good End #1", style: "good", reward: { money: 167556809, respect: 348 } },
            "ge2": { x: 1550, y: 280, type: "end", label: "Good End #2", style: "good", reward: { money: 130168424, respect: 311 } }
        }
    },
    {
        key: "clinical_precision",
        name: "Clinical Precision (Level 8)",
        roles: [
            { id: "cat", name: "Cat Burglar", color: "#ef4444" },  // Red
            { id: "assassin", name: "Assassin", color: "#eab308" }, // Yellow
            { id: "cleaner", name: "Cleaner", color: "#60a5fa" },   // Blue
            { id: "imitator", name: "Imitator", color: "#c084fc" }  // Purple
        ],
        nodes: {
            "start": { x: 60, y: 150, type: "start", next: "c1", label: "START" },

            // Col 1: Cat Burglar
            "c1": { x: 220, y: 150, type: "step", roles: ["cat"], label: "Cat Burglar", color: "#ef4444", pass: "c2", fail: "c1_s1" },
            "c1_s1": { x: 220, y: 280, type: "step", roles: ["assassin", "cat"], label: "Assassin\nCat Burglar", color: "#eab308", pass: "c2", fail: "c1_s2" },
            "c1_s2": { x: 220, y: 410, type: "step", roles: ["cat", "cleaner"], label: "Cat Burglar\nCleaner", color: "#ef4444", pass: "c2", fail: "be1" },
            "be1": { x: 220, y: 540, type: "end", label: "Bad End #1", style: "bad" },

            // Col 2: Assassin
            "c2": { x: 380, y: 150, type: "step", roles: ["assassin"], label: "Assassin", color: "#eab308", pass: "c3", fail: "c2_s1" },
            "c2_s1": { x: 380, y: 280, type: "step", roles: ["assassin"], label: "Assassin", color: "#eab308", pass: "c3", fail: "c3_s2" }, // Fail jumps to deep branch c3_s3

            // Col 3: Cleaner
            "c3": { x: 540, y: 150, type: "step", roles: ["cleaner"], label: "Cleaner", color: "#60a5fa", pass: "c4", fail: "c3_s1" },
            "c3_s1": { x: 540, y: 280, type: "step", roles: ["cleaner"], label: "Cleaner", color: "#60a5fa", pass: "c4", fail: "c3_s2" },
            "c3_s2": { x: 540, y: 410, type: "step", roles: ["imitator"], label: "Imitator", color: "#c084fc", pass: "c4_s2", fail: "c3_s3" },
            "c3_s3": { x: 540, y: 540, type: "step", roles: ["assassin", "cleaner"], label: "Assassin\nCleaner", color: "#eab308", pass: "c4_s2", fail: "be2" },
            "be2": { x: 540, y: 670, type: "end", label: "Bad End #2", style: "bad" },

            // Col 4: Cleaner
            "c4": { x: 700, y: 150, type: "step", roles: ["cleaner"], label: "Cleaner", color: "#60a5fa", pass: "c5", fail: "c4_s1" },
            "c4_s1": { x: 700, y: 280, type: "step", roles: ["cat"], label: "Cat Burglar", color: "#ef4444", pass: "c5", fail: "be3" },
            "be3": { x: 700, y: 410, type: "end", label: "Bad End #3", style: "bad" },

            // Deep branch from c3_s3
            "c4_s2": { x: 700, y: 540, type: "step", roles: ["imitator"], label: "Imitator", color: "#c084fc", pass: "c5_s3", fail: "be4" },
            "be4": { x: 700, y: 670, type: "end", label: "Bad End #4", style: "bad" },

            // Col 5: Imitator
            "c5": { x: 860, y: 150, type: "step", roles: ["imitator"], label: "Imitator", color: "#c084fc", pass: "c7", fail: "c5_s1" },
            "c5_s1": { x: 860, y: 280, type: "step", roles: ["cleaner"], label: "Cleaner", color: "#60a5fa", pass: "c6_s1", fail: "c5_s2" },
            "c5_s2": { x: 860, y: 410, type: "step", roles: ["cat", "cleaner"], label: "Cat Burglar\nCleaner", color: "#ef4444", pass: "c6_s1", fail: "be5" },
            "be5": { x: 860, y: 540, type: "end", label: "Bad End #5", style: "bad" },

            // GE5/6 Branch
            "c5_s3": { x: 860, y: 600, type: "step", roles: ["assassin", "cleaner"], label: "Assassin\nCleaner", color: "#eab308", pass: "ge5", fail: "ge6" },
            "ge5": { x: 1020, y: 560, type: "end", label: "Good End #5", style: "good", reward: { money: 74629714, respect: 179 } },
            "ge6": { x: 1020, y: 640, type: "end", label: "Good End #6", style: "good", reward: { money: 66239666, respect: 154 } },

            // Col 6: Intermediary for lower branch
            "c6_s1": { x: 1020, y: 410, type: "step", roles: ["imitator"], label: "Imitator", color: "#c084fc", pass: "ge4", fail: "be6" },
            "ge4": { x: 1180, y: 350, type: "end", label: "Good End #4", style: "good", reward: { money: 86187142, respect: 209 } },
            "be6": { x: 1180, y: 450, type: "end", label: "Bad End #6", style: "bad" },

            // Col 7: Assassin
            "c7": { x: 1180, y: 150, type: "step", roles: ["assassin"], label: "Assassin", color: "#eab308", pass: "c8", fail: "c7_s1" },
            "c7_s1": { x: 1180, y: 250, type: "step", roles: ["assassin"], label: "Assassin", color: "#eab308", pass: "c8", fail: "c7_s2" },
            // Lowest branch join
            "c7_s2": { x: 1180, y: 550, type: "step", roles: ["imitator"], label: "Imitator", color: "#c084fc", pass: "ge3", fail: "be7" },
            "ge3": { x: 1340, y: 500, type: "end", label: "Good End #3", style: "good", reward: { money: 93822444, respect: 241 } },
            "be7": { x: 1340, y: 600, type: "end", label: "Bad End #7", style: "bad" },

            // Col 8: Assassin/Cleaner
            "c8": { x: 1340, y: 150, type: "step", roles: ["assassin", "cleaner"], label: "Assassin\nCleaner", color: "#eab308", pass: "ge1", fail: "ge2" },
            "ge1": { x: 1550, y: 120, type: "end", label: "Good End #1", style: "good", reward: { money: 117161250, respect: 284 } },
            "ge2": { x: 1550, y: 200, type: "end", label: "Good End #2", style: "good", reward: { money: 104995714, respect: 272 } }
        }
    }
];
