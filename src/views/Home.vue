<template>
  <v-main class="home-main">
    <v-container fluid class="fill-height">
      <v-row class="fill-height" align="center" justify="center">
        <v-col cols="12" sm="8" md="6" lg="4">
          <v-card class="elevation-10 rounded-xl">
            <v-card-title class="justify-center home-title">
              <h1 class="text-h4 font-weight-bold text-center">热字切歌</h1>
            </v-card-title>
            
            <v-card-subtitle class="text-center mt-4">
              选择一位歌手，开始你的游戏
            </v-card-subtitle>
            
            <v-card-text>
              <v-row class="mt-2" justify="center">
                <v-col cols="12" sm="6" class="text-center">
                  <v-hover v-slot="{ isHovering, props }">
                    <v-card
                      v-bind="props"
                      :elevation="isHovering ? 8 : 2"
                      :class="{'on-hover': isHovering}"
                      class="mx-auto artist-card purple-theme"
                      @click="navigateToGame('杨千嬅', '我', 'purple')"
                    >
                      <v-card-title class="justify-center">杨千嬅</v-card-title>
                      <v-card-text class="text-center">
                        <v-avatar size="120" class="mb-4">
                          <v-img src="/assets/杨千嬅.jpg" alt="杨千嬅" 
                                 :class="{'artist-img-hover': isHovering}"
                                 eager
                                 :aspect-ratio="1"
                                 :options="{
                                   quality: 0.8,
                                   width: 180,
                                 }">
                            <template v-slot:placeholder>
                              <v-row class="fill-height" align="center" justify="center">
                                <v-progress-circular indeterminate color="purple"></v-progress-circular>
                              </v-row>
                            </template>
                          </v-img>
                        </v-avatar>
                        <p class="hot-word-text">热字: <span class="hot-word purple">我</span></p>
                      </v-card-text>
                    </v-card>
                  </v-hover>
                </v-col>
                
                <v-col cols="12" sm="6" class="text-center">
                  <v-hover v-slot="{ isHovering, props }">
                    <v-card
                      v-bind="props"
                      :elevation="isHovering ? 8 : 2"
                      :class="{'on-hover': isHovering}"
                      class="mx-auto artist-card red-theme"
                      @click="navigateToGame('张国荣', '你', 'red')"
                    >
                      <v-card-title class="justify-center">张国荣</v-card-title>
                      <v-card-text class="text-center">
                        <v-avatar size="120" class="mb-4">
                          <v-img src="/assets/张国荣.jpg" alt="张国荣"
                                 :class="{'artist-img-hover': isHovering}"
                                 eager
                                 :aspect-ratio="1"
                                 :options="{
                                   quality: 0.8,
                                   width: 180,
                                 }">
                            <template v-slot:placeholder>
                              <v-row class="fill-height" align="center" justify="center">
                                <v-progress-circular indeterminate color="red"></v-progress-circular>
                              </v-row>
                            </template>
                          </v-img>
                        </v-avatar>
                        <p class="hot-word-text">热字: <span class="hot-word red">你</span></p>
                      </v-card-text>
                    </v-card>
                  </v-hover>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </v-main>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const navigateToGame = (artist: string, hotWord: string, theme: string) => {
  router.push({
    name: 'Game',
    params: { artist },
    query: { hotWord, theme }
  })
}
</script>

<style scoped>
.home-main {
  background: linear-gradient(135deg, #f0f6ff, #f5f0ff);
  min-height: 100vh;
}

.home-title {
  background: linear-gradient(to right, #7e57c2, #ef5350);
  color: white !important;
  padding: 20px !important;
  border-radius: 16px 16px 0 0;
}

.artist-card {
  transition: all 0.3s ease;
  border-radius: 16px;
  overflow: hidden;
  border: 2px solid transparent;
  margin-bottom: 16px;
  height: 100%;
}

.artist-card.purple-theme {
  background: linear-gradient(to bottom, #f8f5fe, #f0ebfd);
  border-color: #9575cd;
}

.artist-card.red-theme {
  background: linear-gradient(to bottom, #ffebee, #ffcdd2);
  border-color: #e57373;
}

.on-hover {
  transform: translateY(-8px);
}

.artist-img-hover {
  transform: scale(1.05);
  transition: transform 0.3s ease;
}

.hot-word-text {
  font-size: 1.1rem;
  margin-top: 12px;
}

.hot-word {
  font-weight: bold;
  font-size: 1.4rem;
  padding: 2px 8px;
  border-radius: 4px;
}

.hot-word.purple {
  background-color: #ede7f6;
  color: #7e57c2;
}

.hot-word.red {
  background-color: #ffebee;
  color: #e53935;
}

@media (max-width: 600px) {
  .v-avatar {
    size: 100px;
  }
  
  .home-title {
    padding: 16px !important;
  }
}
</style> 