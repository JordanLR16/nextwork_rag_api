"use client";

import {useState} from "react";
import { BookOpen, ShoppingBasket, PartyPooper, PenLine} from "lucide-react";

const NAV_ITEMS = [
    { icon: BookOpen, label: "Recipes" },
    { icon: ShoppingBasket, label: "Pantry" },
    { icon: PartyPooper, label: "Party" },
    { icon: PenLine, label: "Creation" },
];

export default function Sidebar() {
    const [navActive, setNavActive] = useState(0);
    
    return (
        <aside>
            className="flex flex-col items-center justify-between w-16 py-8 shrink-0 border-r border-border"
            style={{ backgroundColor: "#161618" }}
        </aside> 
    );
}