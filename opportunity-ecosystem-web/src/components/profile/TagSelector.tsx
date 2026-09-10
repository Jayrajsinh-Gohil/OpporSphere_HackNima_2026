"use client";

import React, { useState } from "react";
import { Plus, X, Tag } from "lucide-react";

interface TagSelectorProps {
  label: string;
  placeholder?: string;
  selectedTags: string[];
  onChange: (tags: string[]) => void;
  presets: string[];
  helperText?: string;
  maxTags?: number;
}

export function TagSelector({
  label,
  placeholder = "Type and press Enter...",
  selectedTags,
  onChange,
  presets,
  helperText,
  maxTags = 15,
}: TagSelectorProps) {
  const [inputValue, setInputValue] = useState("");

  const handleAddTag = (tagToAdd: string) => {
    const trimmed = tagToAdd.trim();
    if (!trimmed) return;
    if (selectedTags.some((t) => t.toLowerCase() === trimmed.toLowerCase())) {
      setInputValue("");
      return;
    }
    if (selectedTags.length >= maxTags) return;

    onChange([...selectedTags, trimmed]);
    setInputValue("");
  };

  const handleRemoveTag = (tagToRemove: string) => {
    onChange(selectedTags.filter((t) => t !== tagToRemove));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      handleAddTag(inputValue);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-xs font-medium text-zinc-300">{label}</label>
        <span className="text-xs text-zinc-500">
          {selectedTags.length} / {maxTags} selected
        </span>
      </div>

      {/* Selected Tags Display */}
      <div className="min-h-[48px] p-2.5 rounded-xl bg-zinc-950/70 border border-zinc-800 flex flex-wrap items-center gap-2">
        {selectedTags.length === 0 ? (
          <span className="text-xs text-zinc-500 italic pl-1">
            No items selected yet. Choose from suggestions below or type your own.
          </span>
        ) : (
          selectedTags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 animate-in fade-in zoom-in-95 duration-150"
            >
              <span>{tag}</span>
              <button
                type="button"
                onClick={() => handleRemoveTag(tag)}
                className="hover:text-white p-0.5 rounded transition"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))
        )}
      </div>

      {/* Custom Tag Input */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Tag className="absolute left-3.5 top-3 h-4 w-4 text-zinc-500" />
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="w-full rounded-xl bg-zinc-900 border border-zinc-800 pl-10 pr-4 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
          />
        </div>
        <button
          type="button"
          onClick={() => handleAddTag(inputValue)}
          disabled={!inputValue.trim()}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 disabled:hover:bg-zinc-800 text-xs font-medium text-white transition cursor-pointer"
        >
          <Plus className="h-3.5 w-3.5" />
          <span>Add</span>
        </button>
      </div>

      {/* Suggested Presets */}
      <div>
        <div className="text-[11px] font-medium text-zinc-400 mb-2">Suggested presets (click to toggle):</div>
        <div className="flex flex-wrap gap-1.5">
          {presets.map((preset) => {
            const isSelected = selectedTags.some(
              (t) => t.toLowerCase() === preset.toLowerCase()
            );
            return (
              <button
                key={preset}
                type="button"
                onClick={() =>
                  isSelected ? handleRemoveTag(preset) : handleAddTag(preset)
                }
                className={`px-2.5 py-1 rounded-lg text-xs transition cursor-pointer border ${
                  isSelected
                    ? "bg-indigo-600/30 border-indigo-500 text-indigo-200"
                    : "bg-zinc-900/60 hover:bg-zinc-800 border-zinc-800 text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {isSelected ? "✓ " : "+ "}
                {preset}
              </button>
            );
          })}
        </div>
      </div>

      {helperText && <p className="text-[11px] text-zinc-500 mt-1">{helperText}</p>}
    </div>
  );
}
