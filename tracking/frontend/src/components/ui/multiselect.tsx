import React, { useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { CheckIcon, X } from "lucide-react";

interface Option {
  value: string;
  label: string;
}

interface MultiSelectProps {
  options: Option[];
  placeholder?: string;
  onChange?: (values: string[]) => void;
  selectedValues: string[];
  setSelectedValues: (values: string[]) => void;
  disabled?: boolean;
}

const MultiSelect: React.FC<MultiSelectProps> = ({ 
  options, 
  placeholder = "Select options...",
  selectedValues, 
  setSelectedValues,
  disabled = false
}) => {

  const handleSelect = (value: string) => {
    if (!selectedValues.includes(value)) {
      const newValues = [...selectedValues, value];
      setSelectedValues(newValues);
    }else{
        removeValue(value);
    }
  };

  const removeValue = (valueToRemove: string) => {
    const newValues = selectedValues.filter(value => value !== valueToRemove);
    setSelectedValues(newValues);
  };

  const getOptionLabel = (value: string): string => {
    const option = options.find(opt => opt.value === value);
    return option ? option.label : value;
  };

  return (
    <div className="space-y-2">
      <Select disabled={disabled} value={"NONE"} onValueChange={handleSelect}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder={placeholder}>
            {
                // if no selected values, show the placeholder
                selectedValues.length === 0 ? placeholder :

                selectedValues.length > 2 ? 
                // If more than 2 selected values, show the number of selected values 
                `${selectedValues.length} selected` :
                // Join with a comma 
                selectedValues.map((value) => getOptionLabel(value)).join(", ")
            }
            </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem 
              key={option.value} 
              value={option.value}
            //   disabled={selectedValues.includes(option.value)}
            >
              {option.label} {selectedValues.includes(option.value) && <CheckIcon size={16} />}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {/* {selectedValues.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {selectedValues.map((value) => (
            <div 
              key={value}
              className="flex items-center bg-slate-100 rounded-md px-2 py-1 text-sm"
            >
              <span>{getOptionLabel(value)}</span>
              <button 
                className="ml-1 text-slate-500 hover:text-slate-700"
                onClick={() => removeValue(value)}
                type="button"
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )} */}
    </div>
  );
};


export default MultiSelect;