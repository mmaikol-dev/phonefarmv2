<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('phone_assignments', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('phone_serial');
            $table->timestamps();

            $table->unique(['user_id', 'phone_serial']);
            $table->index('phone_serial');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('phone_assignments');
    }
};
