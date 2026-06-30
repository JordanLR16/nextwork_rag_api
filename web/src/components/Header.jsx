export default function Header() {
  return (
    <div className="flex flex-col flex-1 min-w-0">
        <div className="px-8 pt-6 pb-2 flex items-center justify-between border-b border-border">
            <span
                className= "text-xs text-muted-foreground uppercase"
                style={{ fontFamily: "'DM Mono', monospace" , letterSpacing: "0.15em" }}
            > Jun 26, 2026

            </span>
        </div>
        {/* Category Legend */}
        <div className="hidden md:flex items-center gap-4">
            {[
                { label: "Meat", color: "#4f0904" },
                { label: "Seafood", color: "#5e5757" },
                { label: "Starch", color: "#592802" },
                { label: "Pasta/Veg", color: "#2c5902" },
            ].map(({ label, color }) => (
                <div key={label} className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                    <span
                        className="text-[10px] text-muted-foreground uppercase"
                        style={{ fontFamily: "'DM Mono', monospace", letterSpacing: "0.12em" }}
                    >
                        {label}
                    </span>
            </div>
            ))}
        </div>
    </div>
    );
}